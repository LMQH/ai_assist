#!/bin/bash

# CS Assist AI Backend - 服务管理脚本
# 使用方法: 
#   ./scripts/server.sh start [端口号]     - 启动服务
#   ./scripts/server.sh stop [端口号]      - 停止服务
#   ./scripts/server.sh restart [端口号]   - 重启服务
#   ./scripts/server.sh status [端口号]    - 查看服务状态
#   ./scripts/server.sh config [端口号]    - 更新配置
#   ./scripts/server.sh logs               - 查看日志

set -e

# 获取脚本所在目录的父目录（backend目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${BACKEND_DIR}/config.json"

# conda环境名称
ENV_NAME="cs-assist-ai"

# 获取端口号
get_port() {
    if [ ! -z "$2" ]; then
        echo "$2"
    elif [ -f "${CONFIG_FILE}" ]; then
        python3 -c "import json; f=open('${CONFIG_FILE}'); data=json.load(f); print(data.get('backend', {}).get('port', 8000))" 2>/dev/null || echo "8000"
    else
        echo "8000"
    fi
}

# 更新配置
update_config() {
    local PORT=$1
    echo "🔧 更新配置端口为: ${PORT}..."
    
    # 更新 config.json
    python3 <<EOF
import json
import os

config_file = "${CONFIG_FILE}"
port = ${PORT}

# 读取或创建配置
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
else:
    config = {}

# 更新配置
if 'backend' not in config:
    config['backend'] = {}
config['backend']['port'] = port
config['backend']['host'] = '0.0.0.0'
config['backend']['api_base_url'] = f'http://localhost:{port}'

# 保存配置
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ config.json 已更新")
EOF
}

# 停止服务
stop_server() {
    local PORT=$1
    echo "🛑 停止后端服务（端口: ${PORT}）..."
    
    PID=$(lsof -ti:${PORT} 2>/dev/null || echo "")
    
    if [ -z "$PID" ]; then
        echo "ℹ️  端口 ${PORT} 上没有运行的服务"
        return 0
    fi
    
    echo "📌 找到运行中的服务进程: ${PID}"
    echo "⏳ 正在停止服务..."
    kill $PID 2>/dev/null || true
    sleep 2
    
    if kill -0 $PID 2>/dev/null; then
        echo "⚠️  服务未正常停止，强制停止..."
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    
    if lsof -ti:${PORT} >/dev/null 2>&1; then
        echo "❌ 服务停止失败"
        return 1
    else
        echo "✅ 服务已成功停止（端口: ${PORT}）"
        return 0
    fi
}

# 启动服务
start_server() {
    local PORT=$1
    
    # 如果指定了端口，先更新配置
    if [ ! -z "$2" ]; then
        update_config "$PORT"
    fi
    
    echo "🚀 启动后端服务..."
    echo "📁 后端目录: ${BACKEND_DIR}"
    
    # 检查conda是否安装
    if ! command -v conda &> /dev/null; then
        echo "❌ 错误: 未找到conda，请先安装Anaconda或Miniconda"
        exit 1
    fi
    
    # 初始化conda
    eval "$(conda shell.bash hook)" 2>/dev/null || true
    
    # 激活conda环境
    echo "🔧 激活conda环境: ${ENV_NAME}..."
    conda activate ${ENV_NAME}
    
    # 检查环境是否激活成功
    if [ "$CONDA_DEFAULT_ENV" != "${ENV_NAME}" ]; then
        echo "❌ 错误: conda环境激活失败"
        echo "请先运行: conda activate ${ENV_NAME}"
        exit 1
    fi
    
    # 切换到backend目录
    cd "${BACKEND_DIR}"
    
    # 检查.env文件
    if [ ! -f .env ]; then
        echo "⚠️  警告: 未找到 .env 文件"
        echo "请先创建 .env 文件并填入必要的配置"
        read -p "是否继续启动？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # 检查依赖是否安装
    echo "🔍 检查依赖..."
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "❌ 错误: fastapi未安装"
        echo "请先运行: pip install -r requirements.txt"
        exit 1
    fi
    
    # 检查端口是否被占用
    if lsof -ti:${PORT} >/dev/null 2>&1; then
        echo "⚠️  警告: 端口 ${PORT} 已被占用"
        echo "正在尝试停止现有服务..."
        stop_server "$PORT"
        sleep 2
        if lsof -ti:${PORT} >/dev/null 2>&1; then
            echo "❌ 无法释放端口 ${PORT}，请手动停止占用该端口的进程"
            exit 1
        fi
        echo "✅ 端口已释放"
    fi
    
    # 启动服务
    echo "🌟 启动服务在端口 ${PORT}..."
    echo "📝 访问地址: http://localhost:${PORT}"
    echo "📚 API文档: http://localhost:${PORT}/docs"
    echo "💚 健康检查: http://localhost:${PORT}/health"
    echo ""
    
    # 使用conda环境中的uvicorn启动（后台运行）
    echo "🚀 正在后台启动服务..."
    nohup uvicorn app:app --reload --host 0.0.0.0 --port ${PORT} > "${BACKEND_DIR}/nohup.out" 2>&1 &
    
    # 获取进程ID
    SERVER_PID=$!
    sleep 3
    
    # 检查服务是否启动成功
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ 服务已在后台启动"
        echo "📝 进程ID: ${SERVER_PID}"
        echo "📄 日志文件: ${BACKEND_DIR}/nohup.out"
        echo ""
        echo "查看日志: ./scripts/server.sh logs"
        echo "查看状态: ./scripts/server.sh status"
        echo "停止服务: ./scripts/server.sh stop"
    else
        echo "❌ 服务启动失败，请查看日志: ${BACKEND_DIR}/nohup.out"
        exit 1
    fi
}

# 查看服务状态
show_status() {
    local PORT=$1
    echo "📊 服务状态检查（端口: ${PORT}）..."
    echo ""
    
    PID=$(lsof -ti:${PORT} 2>/dev/null || echo "")
    
    if [ -z "$PID" ]; then
        echo "❌ 服务未运行"
        echo ""
        echo "启动服务: ./scripts/server.sh start"
    else
        echo "✅ 服务正在运行"
        echo "📝 进程ID: ${PID}"
        echo ""
        
        # 尝试获取健康检查信息
        HEALTH_URL="http://localhost:${PORT}/health"
        echo "🔍 健康检查: ${HEALTH_URL}"
        if command -v curl &> /dev/null; then
            HEALTH_RESPONSE=$(curl -s ${HEALTH_URL} 2>/dev/null || echo "")
            if [ ! -z "$HEALTH_RESPONSE" ]; then
                echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
            else
                echo "⚠️  无法连接到服务"
            fi
        fi
    fi
}

# 查看日志
show_logs() {
    local LOG_FILE="${BACKEND_DIR}/nohup.out"
    
    if [ ! -f "$LOG_FILE" ]; then
        echo "❌ 日志文件不存在: ${LOG_FILE}"
        exit 1
    fi
    
    echo "📄 显示日志（按 Ctrl+C 退出）..."
    echo "日志文件: ${LOG_FILE}"
    echo ""
    tail -f "$LOG_FILE"
}

# 显示帮助信息
show_help() {
    cat <<EOF
CS Assist AI Backend - 服务管理脚本

使用方法:
  ./scripts/server.sh <命令> [选项]

命令:
  start [端口号]             启动服务（默认从配置文件读取端口）
  stop [端口号]              停止服务
  restart [端口号]           重启服务
  status [端口号]            查看服务状态
  config [端口号]            更新配置端口号
  logs                       查看实时日志
  help                       显示帮助信息

示例:
  ./scripts/server.sh start                    # 使用配置文件中的端口启动
  ./scripts/server.sh start 8003               # 在8003端口启动并更新配置
  ./scripts/server.sh stop                     # 停止服务
  ./scripts/server.sh restart                  # 重启服务
  ./scripts/server.sh status                   # 查看服务状态
  ./scripts/server.sh config 8003              # 更新配置端口为8003
  ./scripts/server.sh logs                     # 查看实时日志

配置文件: ${CONFIG_FILE}
日志文件: ${BACKEND_DIR}/nohup.out
EOF
}

# 主逻辑
COMMAND=${1:-help}
PORT=$(get_port "$@")

case "$COMMAND" in
    start)
        start_server "$PORT" "$2"
        ;;
    stop)
        stop_server "$PORT"
        ;;
    restart)
        echo "🔄 重启服务..."
        stop_server "$PORT"
        sleep 2
        start_server "$PORT"
        ;;
    status)
        show_status "$PORT"
        ;;
    config)
        if [ -z "$2" ]; then
            echo "❌ 错误: 请指定端口号"
            echo "使用方法: ./scripts/server.sh config <端口号>"
            exit 1
        fi
        update_config "$2"
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac

