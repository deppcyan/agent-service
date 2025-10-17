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

2. Wan I2V 服务， model name: wan-i2v, 输入的话，是图片+prompt
3. Wan InfiniteTalk + VibeVoice服务, model name: wan-talk， 输入的话，是图片 prompt audio_prompt
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
    "model": "concat-upscale",
    "input": [
        {
            "type": "video",
            "url": "string"
        },
        {
            "type": "video",
            "url": "string"
        }
    ],
    "options": {
        
    },
    "webhookUrl": "string"
}

webhook回调

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
    "https://xxx.mp4"
  ]
  "error": null
}

----
实现了上述节点的纹身，workflow的整个工作流程是：
1. 将用户输入的图片以及prompt，调用qwen vl模型，system prompt如下：
【输入方式】：参考图 + 文本描述  
【延展目标】：基于上一张图的画面风格、人物外形、光影氛围、镜头语言，生成下一张分镜图，使得剧情延续

保持人物外观一致  
色调光影与参考图统一  
背景元素延续，不突变  
构图具备电影感（景别 / 光影 / 空间层次）

镜头类型（特写 / 中景 / 远景 / 俯拍 / 跟拍 / 环绕 / 侧移 / 拉远）  
镜头运动节奏（慢推 / 快切 / 手持感）  

人物发色、身形不变  
服饰延续衔接，不跳变  
动作表情是上一个镜头的自然推进  
背景环境连续递进

高清画面  
电影级光影  
真实材质  
无噪点无畸变  
可作为下一张分镜生成基础

输出时以Next Scene:开头，后面马上接文字。每一段文字是连续的，没有特殊符号，没有多余的解释，每一段文字100字左右，直接输出内容

输出话会是这样的

{
    "status": "success",
    "enhanced_prompt": "Next Scene: 镜头切换到一片战场，士兵们穿着厚重的军装，手持步枪，表情严肃。天空阴沉，远处炮火连天，烟雾弥漫。\n\nNext Scene: 战斗激烈，士兵们在战壕中匍匐前进，子弹横飞，血迹斑斑。士兵们的表情坚毅，眼神中透露出对胜利的渴望。\n\nNext Scene: 一名士兵在夜幕中潜行，月光洒在沙地上，他手持手电筒，照亮前方的道路。背景中传来沉重的脚步声，敌人正在逼近。\n\nNext Scene: 士兵们在废墟中坚守阵地，枪声不断，弹片四溅。他们互相鼓励，用血肉之躯筑起防线，对抗着敌人的进攻。\n\nNext Scene: 在一个废弃的工厂内，几名士兵正在进行紧急部署。指挥官下达命令，士兵们迅速行动，准备反击。",
    "original_prompt": "在二战中战斗的故事",
    "processing_time": 3.586752,
    "seed": 1218481370
}
---
解析Next Scene:，然后提取出来，作为关键帧的提示词，最多提取3帧。
2. 根据关键帧的系统提示词调用Qwen Edit来生图，输入是用户输入的图片以及提取出来的提示词，输出是对应的图片。
3. 输入关键帧图片以及提示词，调用wan-i2v服务，来生成视频。
4. 获取上述视频片段然后调用合并视频服务，来生成最终视频。
5. 通过file_manager生成local地址，如果有s3地址，则上传到对应的s3地址上，然后回调webhook。