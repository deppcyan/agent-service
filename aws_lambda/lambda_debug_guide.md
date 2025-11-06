# AWS Lambda 调试和监控指南

## 1. 默认库说明

### ✅ AWS Lambda Python 运行时默认包含的库：
- `boto3` - AWS SDK for Python
- `botocore` - boto3的底层库
- `json`, `os`, `logging` 等Python标准库

### ❌ 需要手动安装的库：
- `urllib3` - HTTP客户端库
- 其他第三方库

## 2. 本地调试方法

### 方法1：使用本地测试脚本（推荐）

```bash
# 运行本地测试脚本
python test_lambda_local.py
```

这个脚本会：
- 模拟S3事件
- 模拟AWS服务调用
- 测试Lambda函数逻辑
- 显示详细的执行日志

### 方法2：使用AWS SAM CLI

1. **安装AWS SAM CLI**：
```bash
# macOS
brew install aws-sam-cli

# Linux
pip install aws-sam-cli
```

2. **创建SAM模板** (`template.yaml`):
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ConfigNotifierFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: aws_lambda/
      Handler: lambda_function.lambda_handler
      Runtime: python3.9
      Environment:
        Variables:
          API_KEY: your-test-api-key
      Events:
        S3Event:
          Type: S3
          Properties:
            Bucket: !Ref S3Bucket
            Events: s3:ObjectCreated:*
            Filter:
              S3Key:
                Rules:
                  - Name: suffix
                    Value: .json

  S3Bucket:
    Type: AWS::S3::Bucket
```

3. **本地调用**：
```bash
# 构建
sam build

# 本地调用
sam local invoke ConfigNotifierFunction -e test-event.json

# 本地API网关
sam local start-api
```

### 方法3：使用VS Code AWS Toolkit

1. 安装AWS Toolkit扩展
2. 配置AWS凭证
3. 右键Lambda函数 → "Invoke on AWS"
4. 设置断点进行远程调试

## 3. 查看Lambda函数状态

### 3.1 AWS控制台监控

1. **进入Lambda控制台**：
   - AWS Console → Lambda → Functions → 选择你的函数

2. **监控选项卡**：
   - 调用次数
   - 持续时间
   - 错误率
   - 成功率

3. **日志选项卡**：
   - 查看CloudWatch日志
   - 实时日志流

### 3.2 使用AWS CLI检查状态

```bash
# 获取函数信息
aws lambda get-function --function-name config-notify

# 获取函数配置
aws lambda get-function-configuration --function-name config-notify

# 列出函数版本
aws lambda list-versions-by-function --function-name config-notify

# 调用函数测试
aws lambda invoke \
  --function-name config-notify \
  --payload file://test-event.json \
  response.json
```

### 3.3 查看CloudWatch日志

```bash
# 查看日志组
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/config-notify

# 实时查看日志
aws logs tail /aws/lambda/config-notify --follow

# 查看特定时间段的日志
aws logs filter-log-events \
  --log-group-name /aws/lambda/config-notify \
  --start-time 1699200000000 \
  --end-time 1699286400000
```

## 4. 常见问题排查

### 4.1 函数未触发
```bash
# 检查S3事件配置
aws s3api get-bucket-notification-configuration --bucket your-bucket-name

# 检查Lambda权限
aws lambda get-policy --function-name agent-service-config-notifier
```

### 4.2 权限问题
```bash
# 检查执行角色
aws iam get-role --role-name agent-service-lambda-role

# 检查角色策略
aws iam list-attached-role-policies --role-name agent-service-lambda-role
```

### 4.3 网络问题
```bash
# 检查VPC配置（如果使用VPC）
aws lambda get-function-configuration --function-name agent-service-config-notifier --query VpcConfig
```

## 5. 性能监控

### 5.1 CloudWatch指标

重要指标：
- `Duration` - 执行时间
- `Invocations` - 调用次数
- `Errors` - 错误次数
- `Throttles` - 限流次数
- `ConcurrentExecutions` - 并发执行数

### 5.2 设置告警

```bash
# 创建错误率告警
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-Errors-agent-service-config-notifier" \
  --alarm-description "Lambda function error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=agent-service-config-notifier \
  --evaluation-periods 1
```

## 6. 调试最佳实践

### 6.1 日志记录
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 在关键位置添加日志
logger.info(f"Processing S3 event: {event}")
logger.error(f"Error occurred: {str(e)}")
```

### 6.2 错误处理
```python
try:
    # 主要逻辑
    pass
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    # 返回适当的错误响应
    return {
        'statusCode': 500,
        'body': json.dumps({'error': str(e)})
    }
```

### 6.3 测试事件模板

创建 `test-event.json`:
```json
{
  "Records": [
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "awsRegion": "us-west-1",
      "eventTime": "2025-11-06T12:00:00.000Z",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "your-bucket-name"
        },
        "object": {
          "key": "config.json"
        }
      }
    }
  ]
}
```

## 7. 部署后验证清单

- [ ] 函数状态为 "Active"
- [ ] 环境变量正确设置
- [ ] S3触发器配置正确
- [ ] IAM权限充足
- [ ] CloudWatch日志正常记录
- [ ] 测试事件执行成功
- [ ] 外部API调用正常

使用这些方法，你可以全面监控和调试AWS Lambda函数的运行状态。

{
  "configVersion": 4,
  "appId": "agent-service",
  "notifications": {
    "targets": [
      {
        "url": "http://54.177.45.79:8000/config/refresh",
        "type": "pod",
        "apiKey": "TEST_API_KEY"
      }
    ]
  },
  "appConfig": {
    "versions": {
      "all": {
        "files": [
          {
            "appPath": "config/audio/voice_list.json",
            "s3Path": "https://digen-app-config.s3.us-west-1.amazonaws.com/agent-service/audio/voice_list.json",
            "version": 2
          }
        ]
      }
    }
  }
}