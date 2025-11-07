#!/bin/bash

# Docker部署脚本
# 功能：拉取镜像、停止旧容器、启动新容器并配置环境变量

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 默认配置
DEFAULT_IMAGE="deppcyan/agent-service:latest"
DEFAULT_CONTAINER_NAME="agent-service"
DEFAULT_PORT="8000"

# 显示使用说明
show_usage() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -i, --image IMAGE_NAME      指定Docker镜像 (默认: $DEFAULT_IMAGE)"
    echo "  -n, --name CONTAINER_NAME   指定容器名称 (默认: $DEFAULT_CONTAINER_NAME)"
    echo "  -p, --port PORT             指定端口映射 (默认: $DEFAULT_PORT)"
    echo "  -h, --help                  显示此帮助信息"
    echo ""
    echo "环境变量 (必须设置):"
    echo "  AWS_ACCESS_KEY_ID"
    echo "  AWS_SECRET_ACCESS_KEY"
    echo "  WASABI_ACCESS_KEY_ID"
    echo "  WASABI_SECRET_ACCESS_KEY"
    echo "  DIGEN_SERVICE_URL"
    echo "  DIGEN_SERVICE_IP"
    echo "  DIGEN_SERVICES_API_KEY"
    echo "  DIGEN_SERVICE_ENV"
    echo ""
    echo "示例:"
    echo "  $0 -i deppcyan/agent-service:1.0.2 -n my-agent-service -p 8080"
}

# 检查必需的环境变量
check_env_vars() {
    local required_vars=(
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "WASABI_ACCESS_KEY_ID"
        "WASABI_SECRET_ACCESS_KEY"
        "DIGEN_SERVICE_URL"
        "DIGEN_SERVICE_IP"
        "DIGEN_SERVICES_API_KEY"
        "DIGEN_SERVICE_ENV"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必需的环境变量:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "请设置这些环境变量后重新运行脚本。"
        echo "例如: export AWS_ACCESS_KEY_ID=your_access_key"
        exit 1
    fi
    
    log_success "所有必需的环境变量已设置"
}

# 检查Docker是否安装并运行
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "Docker检查通过"
}

# 拉取Docker镜像
pull_image() {
    local image=$1
    log_info "正在拉取镜像: $image"
    
    if docker pull "$image"; then
        log_success "镜像拉取成功: $image"
    else
        log_error "镜像拉取失败: $image"
        exit 1
    fi
}

# 停止并删除现有容器
stop_existing_container() {
    local container_name=$1
    
    # 检查容器是否存在
    if docker ps -a --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        log_info "发现现有容器: $container_name"
        
        # 如果容器正在运行，先停止它
        if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
            log_info "正在停止运行中的容器: $container_name"
            docker stop "$container_name"
            log_success "容器已停止: $container_name"
        fi
        
        # 删除容器
        log_info "正在删除容器: $container_name"
        docker rm "$container_name"
        log_success "容器已删除: $container_name"
    else
        log_info "未发现名为 $container_name 的现有容器"
    fi
}

# 启动新容器
start_container() {
    local image=$1
    local container_name=$2
    local port=$3
    
    log_info "正在启动新容器..."
    log_info "镜像: $image"
    log_info "容器名: $container_name"
    log_info "端口映射: $port:8000"
    
    # 构建docker run命令
    local docker_cmd="docker run -d \
        --name $container_name \
        -p $port:8000 \
        --network host \
        --restart unless-stopped \
        -e AWS_ACCESS_KEY_ID=\"$AWS_ACCESS_KEY_ID\" \
        -e AWS_SECRET_ACCESS_KEY=\"$AWS_SECRET_ACCESS_KEY\" \
        -e WASABI_ACCESS_KEY_ID=\"$WASABI_ACCESS_KEY_ID\" \
        -e WASABI_SECRET_ACCESS_KEY=\"$WASABI_SECRET_ACCESS_KEY\" \
        -e DIGEN_SERVICE_URL=\"$DIGEN_SERVICE_URL\" \
        -e DIGEN_SERVICE_IP=\"$DIGEN_SERVICE_IP\" \
        -e DIGEN_SERVICES_API_KEY=\"$DIGEN_SERVICES_API_KEY\" \
        -e DIGEN_SERVICE_ENV=\"$DIGEN_SERVICE_ENV\" \
        $image"
    
    # 执行命令
    if eval $docker_cmd; then
        log_success "容器启动成功: $container_name"
        
        # 等待几秒钟让容器完全启动
        sleep 3
        
        # 检查容器状态
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "^${container_name}"; then
            log_success "容器运行状态正常"
            docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep "$container_name"
        else
            log_error "容器启动后状态异常，请检查日志:"
            docker logs "$container_name"
            exit 1
        fi
    else
        log_error "容器启动失败"
        exit 1
    fi
}

# 显示容器日志
show_logs() {
    local container_name=$1
    log_info "显示容器日志 (最后20行):"
    docker logs --tail 20 "$container_name"
}

# 主函数
main() {
    local image="$DEFAULT_IMAGE"
    local container_name="$DEFAULT_CONTAINER_NAME"
    local port="$DEFAULT_PORT"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--image)
                image="$2"
                shift 2
                ;;
            -n|--name)
                container_name="$2"
                shift 2
                ;;
            -p|--port)
                port="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    log_info "开始Docker部署流程..."
    log_info "镜像: $image"
    log_info "容器名: $container_name"
    log_info "端口: $port"
    echo ""
    
    # 执行部署步骤
    check_docker
    check_env_vars
    pull_image "$image"
    stop_existing_container "$container_name"
    start_container "$image" "$container_name" "$port"
    
    echo ""
    log_success "部署完成！"
    log_info "容器访问地址: http://localhost:$port"
    log_info "查看日志命令: docker logs -f $container_name"
    log_info "停止容器命令: docker stop $container_name"
    
    # 询问是否显示日志
    echo ""
    read -p "是否显示容器日志？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs "$container_name"
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
