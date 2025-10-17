import os
import asyncio
from typing import Dict, Any, List, Optional
import aiohttp
from .base import AsyncWorkflow
from ..core.logger import logger
from ..core.storage.downloader import downloader
from ..core.storage.uploader import uploader
from ..core.storage.file_manager import input_file_manager, output_file_manager
from ..core.job_manager import job_manager
from ..core.utils import process_image
from ..core.concurrency import concurrency_manager

class ImageToVideoWorkflow(AsyncWorkflow):
    """Async workflow for image to video generation"""
    
    def __init__(self):
        super().__init__("image_to_video")
    
    async def download_inputs(self, job_id: str) -> Dict[str, str]:
        """Download input files"""
        job_state = job_manager.get_job_state(job_id)
        if not job_state:
            raise ValueError(f"Job {job_id} not found")
        
        input_files = {}
        try:
            download_tasks = []
            for idx, input_item in enumerate(job_state.input):
                # Check cache first
                cached_path = input_file_manager.get_cached_file(input_item["url"])
                if cached_path:
                    input_files[f"input_{idx}"] = cached_path
                    continue
                
                # Prepare download task
                file_ext = os.path.splitext(input_item["url"])[1] or ".bin"
                local_path = f"storage/inputs/{job_id}_{idx}{file_ext}"
                task = asyncio.create_task(
                    downloader.download(input_item["url"], local_path, job_id)
                )
                download_tasks.append((idx, task))
            
            # Wait for all downloads to complete
            for idx, task in download_tasks:
                try:
                    downloaded_path = await task
                    # Cache the file
                    cached_path = await input_file_manager.cache_file(
                        job_state.input[idx]["url"],
                        downloaded_path
                    )
                    input_files[f"input_{idx}"] = cached_path
                except Exception as e:
                    raise Exception(f"Failed to download input {idx}: {str(e)}")
            
            return input_files
            
        except Exception as e:
            # Clean up on error
            for path in input_files.values():
                try:
                    os.remove(path)
                except:
                    pass
            raise Exception(f"Failed to download input files: {str(e)}")
    
    async def _call_service(self, service: str, url: str, headers: Dict[str, str], 
                           data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Make async HTTP call to service with rate limiting and retries"""
        async def _make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Service call failed with status {response.status}: {error_text}")
                    return await response.json()
        
        return await concurrency_manager.execute_with_limits(
            service,
            _make_request,
            job_id=job_id
        )
    
    async def process_job(self, job_id: str, input_files: Dict[str, str]) -> Dict[str, str]:
        """Process the job through multiple services"""
        job_state = job_manager.get_job_state(job_id)
        if not job_state:
            raise ValueError(f"Job {job_id} not found")
        
        try:
            # Process main input image
            main_image = input_files["input_0"]
            width, height, adj_h, adj_w, lat_h, lat_w = await process_image(
                main_image,
                job_id,
                job_state.options
            )
            
            # Call QwenVL for scene generation
            qwen_response = await self._call_service(
                "qwen-vl",
                f"{job_state.options['qwen_vl_url']}/v1/generate",
                {"X-API-Key": job_state.options["api_key"]},
                {
                    "image_url": job_state.input[0]["url"],
                    "prompt": job_state.options.get("prompt", ""),
                    "system_prompt": job_state.options.get("system_prompt", "")
                },
                job_id
            )
            
            # Extract scenes
            scenes = self._extract_scenes(qwen_response["enhanced_prompt"])
            
            # Generate images for each scene in parallel
            edit_tasks = []
            for scene in scenes:
                task = asyncio.create_task(
                    self._call_service(
                        "qwen-edit",
                        f"{job_state.options['qwen_edit_url']}/v1/generate",
                        {"X-API-Key": job_state.options["api_key"]},
                        {
                            "model": "qwen-edit",
                            "input": [{"type": "image", "url": job_state.input[0]["url"]}],
                            "options": {
                                "prompt": scene,
                                "width": adj_w,
                                "height": adj_h
                            }
                        },
                        job_id
                    )
                )
                edit_tasks.append(task)
            
            edited_images = await asyncio.gather(*edit_tasks)
            
            # Generate videos for each image in parallel
            video_tasks = []
            for idx, (image, scene) in enumerate(zip(edited_images, scenes)):
                task = asyncio.create_task(
                    self._call_service(
                        "wan-i2v",
                        f"{job_state.options['wan_i2v_url']}/v1/generate",
                        {"X-API-Key": job_state.options["api_key"]},
                        {
                            "model": "wan-i2v",
                            "input": [{"type": "image", "url": image["localUrl"][0]}],
                            "options": {
                                "prompt": scene,
                                "width": adj_w,
                                "height": adj_h,
                                "duration": job_state.options.get("duration", 5)
                            }
                        },
                        job_id
                    )
                )
                video_tasks.append((idx, task))
            
            # Download videos in parallel
            video_files = []
            for idx, task in video_tasks:
                response = await task
                video_path = f"storage/outputs/{job_id}_video_{idx}.mp4"
                await downloader.download(response["localUrl"][0], video_path, job_id)
                video_files.append(video_path)
            
            # Concatenate videos
            concat_response = await self._call_service(
                "video-concat",
                f"{job_state.options['video_concat_url']}/v1/generate",
                {"X-API-Key": job_state.options["api_key"]},
                {
                    "model": "concat-upscale",
                    "input": [{"type": "video", "url": path} for path in video_files],
                    "options": {
                        "crf": job_state.options.get("crf", None)
                    }
                },
                job_id
            )
            
            # Download final video
            final_video_path = f"storage/outputs/{job_id}_final.mp4"
            await downloader.download(
                concat_response["localUrl"][0],
                final_video_path,
                job_id
            )
            
            return {"final": final_video_path}
            
        except Exception as e:
            raise Exception(f"Failed to process job: {str(e)}")
    
    def _extract_scenes(self, text: str, max_scenes: int = 3) -> List[str]:
        """Extract scene descriptions from QwenVL output"""
        scenes = []
        for line in text.split("\n"):
            if line.startswith("Next Scene:"):
                scenes.append(line.replace("Next Scene:", "").strip())
                if len(scenes) >= max_scenes:
                    break
        return scenes
    
    async def upload_outputs(self, job_id: str, output_files: Dict[str, str]) -> Dict[str, str]:
        """Upload output files"""
        job_state = job_manager.get_job_state(job_id)
        if not job_state:
            raise ValueError(f"Job {job_id} not found")
        
        try:
            urls = {}
            final_video = output_files["final"]
            upload_tasks = []
            
            # Prepare upload tasks
            if job_state.options.get("upload_url"):
                task = asyncio.create_task(
                    uploader.upload(
                        final_video,
                        job_id,
                        custom_url=job_state.options["upload_url"],
                        content_type="video/mp4"
                    )
                )
                upload_tasks.append(("aws", task))
            
            if job_state.options.get("upload_wasabi_url"):
                task = asyncio.create_task(
                    uploader.upload(
                        final_video,
                        job_id,
                        custom_url=job_state.options["upload_wasabi_url"],
                        content_type="video/mp4"
                    )
                )
                upload_tasks.append(("wasabi", task))
            
            # Wait for uploads to complete
            for provider, task in upload_tasks:
                try:
                    urls[provider] = await task
                except Exception as e:
                    logger.error(f"Failed to upload to {provider}: {str(e)}", 
                               extra={"job_id": job_id})
            
            # Store locally
            local_file_id = await output_file_manager.store_file(final_video, job_id)
            urls["local"] = f"/files/{local_file_id}"
            
            return urls
            
        except Exception as e:
            raise Exception(f"Failed to upload output files: {str(e)}")

# Create workflow instance
image_to_video_workflow = ImageToVideoWorkflow()