# AI Service Workflow Framework

A flexible workflow framework for executing AI service pipelines, built with FastAPI and Langchain.

## Features

- Modular workflow system with pluggable service nodes
- Support for multiple AI services (QwenVL, WanI2V, QwenEdit, etc.)
- Asynchronous execution with webhook support
- File management with local and S3 storage
- Cancellable workflows and jobs

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```
5. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Start Workflow
```http
POST /v1/workflow/generate
Content-Type: application/json

{
    "image_url": "https://example.com/image.jpg",
    "prompt": "Optional prompt",
    "webhook_url": "https://your-webhook-url.com"
}
```

### Cancel Workflow
```http
POST /v1/workflow/cancel
Content-Type: application/json

{
    "workflow_id": "workflow_id_here"
}
```

## Project Structure

```
app/
├── core/
│   ├── base.py         # Base classes for workflow and services
│   ├── config.py       # Configuration management
│   └── file_manager.py # File handling utilities
├── services/
│   └── nodes.py        # Service node implementations
├── workflows/
│   └── image_to_video.py # Image to video workflow implementation
└── main.py             # FastAPI application
```

## Adding New Workflows

1. Create a new workflow class inheriting from `Workflow`
2. Implement the required methods
3. Add necessary service nodes
4. Register the workflow in `main.py`

## Environment Variables

- `API_KEY`: API key for all services
- `QWEN_VL_URL`: QwenVL service URL
- `WAN_I2V_URL`: WanI2V service URL
- `WAN_TALK_URL`: WanTalk service URL
- `QWEN_EDIT_URL`: QwenEdit service URL
- `VIDEO_CONCAT_URL`: Video concatenation service URL
- `S3_BUCKET`: S3 bucket name
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
