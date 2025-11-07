# Docker 部署脚本使用说明

## 概述

`deploy.sh` 脚本提供了完整的 Docker 容器部署解决方案，包括：
1. 拉取指定的 Docker 镜像
2. 停止并删除现有的运行容器
3. 使用配置的环境变量启动新容器

## 使用方法

### 基本用法

```bash
./deploy.sh
```

### 带参数使用

```bash
./deploy.sh -i deppcyan/agent-service:1.0.2 -n my-agent-service -p 8080
```

### 参数说明

- `-i, --image IMAGE_NAME`: 指定 Docker 镜像 (默认: deppcyan/agent-service:latest)
- `-n, --name CONTAINER_NAME`: 指定容器名称 (默认: agent-service)
- `-p, --port PORT`: 指定端口映射 (默认: 8000)
- `-h, --help`: 显示帮助信息

## 环境变量配置

在运行脚本之前，必须设置以下环境变量：

### AWS 配置
```bash
export AWS_ACCESS_KEY_ID="your_aws_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"
```

### Wasabi 配置
```bash
export WASABI_ACCESS_KEY_ID="your_wasabi_access_key_id"
export WASABI_SECRET_ACCESS_KEY="your_wasabi_secret_access_key"
```

### DIGEN 服务配置
```bash
export DIGEN_SERVICE_URL="http://your-digen-service-url"
export DIGEN_SERVICE_IP="your.digen.service.ip"
export DIGEN_SERVICES_API_KEY="your_digen_api_key"
export DIGEN_SERVICE_ENV="production"
```

## 推荐的使用流程

### 1. 创建环境变量文件

创建一个 `env.sh` 文件来管理环境变量：

```bash
#!/bin/bash
# env.sh - 环境变量配置

export AWS_ACCESS_KEY_ID="your_aws_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"
export WASABI_ACCESS_KEY_ID="your_wasabi_access_key_id"
export WASABI_SECRET_ACCESS_KEY="your_wasabi_secret_access_key"
export DIGEN_SERVICE_URL="http://your-digen-service-url"
export DIGEN_SERVICE_IP="your.digen.service.ip"
export DIGEN_SERVICES_API_KEY="your_digen_api_key"
export DIGEN_SERVICE_ENV="production"
```

### 2. 加载环境变量并部署

```bash
# 加载环境变量
source env.sh

# 执行部署
./deploy.sh -i deppcyan/agent-service:1.0.2
```

### 3. 一键部署脚本

创建一个 `quick-deploy.sh` 文件：

```bash
#!/bin/bash
# 加载环境变量
source env.sh

# 执行部署
./deploy.sh -i deppcyan/agent-service:1.0.2 -n agent-service -p 8000
```

## 脚本功能特性

### 安全检查
- 检查 Docker 是否安装并运行
- 验证所有必需的环境变量是否设置
- 错误时自动退出，避免部分部署

### 智能容器管理
- 自动检测并停止现有容器
- 清理旧容器避免冲突
- 支持容器重启策略

### 用户友好
- 彩色日志输出
- 详细的进度提示
- 部署完成后的状态检查
- 可选的日志查看

### 错误处理
- 完整的错误检查和提示
- 失败时的详细错误信息
- 容器启动异常时的日志输出

## 常见问题

### Q: 如何查看容器日志？
```bash
docker logs -f agent-service
```

### Q: 如何停止容器？
```bash
docker stop agent-service
```

### Q: 如何重新部署？
```bash
# 直接运行脚本即可，会自动停止旧容器并启动新容器
./deploy.sh -i deppcyan/agent-service:1.0.3
```

### Q: 环境变量设置错误怎么办？
重新设置环境变量后再次运行脚本即可：
```bash
export AWS_ACCESS_KEY_ID="correct_value"
./deploy.sh
```

## 注意事项

1. 确保 Docker 服务正在运行
2. 确保有足够的权限执行 Docker 命令
3. 网络连接正常，能够拉取镜像
4. 端口未被其他服务占用
5. 环境变量中不要包含特殊字符，如有需要请适当转义
