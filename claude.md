写一个程序，是一个执行workflow的框架。根据用户的请求，自动执行相应的workflow，每个workflow包含多个执行步骤，例如大模型，生视频，生图服务，视频合成服务等。
要求灵活一点，扩展性强一点，不仅是一个workflow，也可以执行多个workflow，添加一个workflow非常容易。
可以基于langchain框架来实现，根据请求中的modle名字来执行不同的workflow。
框架的要求如上，目前首先要实现的一个workflow如下：
首先要实现的服务节点如下：
1. Qwen VL 模型服务, model name: qwen-vl

请求api如下
/v1/generate

X-API-Key: xxx
Content-Type: application/json

{
    "image_url": "https://lipsync-video.s3.us-west-1.amazonaws.com/test.jpeg",
    "prompt": "",  #可选，用户的提示词，可不填
    "system_prompt": "", #可选，系统提示词,如果使用默认的系统提示词，不要传此字段。
}

返回
{
    "status": "success",
    "enhanced_prompt": "prompt",
    "original_prompt": "",
    "processing_time": 1.3061485290527344,
    "seed": 979894236
}

2. Wan I2V + MMAudio 服务， model name: wan-i2v, 输入的话，是图片+prompt
3. Wan InfiniteTalk + VibeVoice服务, model name: wan-talk， 输入的话，是图片+prompt
4. Qwen Edit 图片编辑服务, model name: qwen-edit，输入的话，是图片+prompt

生成接口如下
/v1/generate

X-API-Key: xxx
Content-Type: application/json

{
  "model": "qwen-i2v",
  "input": [
        {
            "type": "image", 
            "url": "string" //对于kontext模型需要输入
        }
    ],
  "options": {
    "prompt": "你的提示词", 
    "width": 768,
    "height": 768,
    "batch_size": 1,
    "output_format": "jpeg", // 生成图片格式，可选
    "webp_quality": 90, //生成图片的质量,可选
    "seed": 32323, //种子，可选
  },
  "webhookUrl": "https://your-webhook-url.com"
}

返回

{
    "id": "9fff5c68-3877-4f96-8231-3e464422a72e",
    "pod_id": "fbnfm6e36rm5o7", // pid id
    "queuePosition": 1, //排队位置
    "estimatedWaitTime": 130.240256, //预估需要生成视频所需的时间
    "pod_url": "https://wq2542euu4aef0-8000.proxy.runpod.net"
}

webhook 回调

{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "createdAt": "2024-03-21T10:00:00Z",
  "status": "completed",
  "model": "qwen-i2v",
  "webhookUrl": "https://your-webhook-url.com",
  "options": {
    // 原始请求中的 options
  },
  "stream": true,
  "localUrl": [
    "https://xxx.jpeg"
  ]
  "error": null
}

上述服务的取消接口
/cancel/{job_id}
- 任务不存在或者任务正在生成，会返回404错误
- 成功删除返回200
{
    "status": "cancelled",
    "job_id": job_id
}

将上述4个服务封装成接口，抽象所有服务都有一个取消接口，用于取消整个workflow。
服务url，从配置中读取，apk key的话，所有的key都是一样的，从环境变量中读取。
5. 将生成的视频片段合成一个视频的服务
/v1/generate

X-API-Key: xxx
Content-Type: application/json

{
    "model": "watermarkv1.0",
    "input": [
        {
            "type": "clip",
            "url": "string"
        },
        {
            "type": "clip",
            "url": "string"
        }
    ],
    "options": {
        "add_watermark": "true",
        "upload_url": "https://digen-asset.s3.us-west-1.amazonaws.com/audio/173325_1740704056423951010_a959611e-7014-4b9a-94d2-b00be07b985b.mp4"，
        "original_video_url": "https://digen-asset.s3.us-west-1.amazonaws.com/audio/173325_1740704056423951010_a959611e-7014-4b9a-94d2-b00be07b985b.mp4"
        "set_crf": true,
        "crf_value": 28,
        "upload_wasabi_url": "https://s3.us-west-1.wasabisys.com/gen-bp/test6.mp4",
        "watermark_url": "", // 自定义的水印图片的s3地址
        "watermark_width": 333, // 自定义水印图片在视频中展示的宽
        "watermark_height": 39,  // 自定义水印图片在视频中展示的高
        "watermark_max_ratio": 0.5, // 水印图片的宽占视频宽的最大比例
        "first_frame_url": "", // 首帧生成的s3地址，如果没有地址的话，默认不生成首帧
        "first_frame_max_size": 1024 // 首帧图片生成的最大的边长
    },
    "webhookUrl": "string"
}

webhook回调

{
    "id": "string",
    "createdAt": 1739950001.2138739,
    "status": "completed",
    "model": "string",
    "input": [
        {
            "type": "string",
            "url": "string"
        }
    ],
    "webhookUrl": "string",
    "options": {
        "output_format": "string"，
    },
    "stream": true,
    "outputUrl": "string",
    "outputWasabiUrl": "string", //上传失败为空
    "firstFrameUrl": "string", //返回的首帧地址
    "error": null
}

