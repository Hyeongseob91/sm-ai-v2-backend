#!/bin/bash
# MCP Servers 시작 스크립트
#
# 사용법:
#   ./scripts/start_mcp_servers.sh [all|chart|echarts|stop|status]
#
# 사전 요구사항:
#   - Node.js 18+ (npx 사용)
#   - npm install -g mcp-echarts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# AntV MCP Server Chart 시작 (포트 1122)
start_chart_server() {
    log_info "Starting @antv/mcp-server-chart on port 1122..."

    # 기존 프로세스 확인
    if pgrep -f "mcp-server-chart" > /dev/null; then
        log_warn "mcp-server-chart is already running"
        return 0
    fi

    nohup npx -y @antv/mcp-server-chart --transport sse \
        > "$LOG_DIR/mcp-server-chart.log" 2>&1 &

    sleep 2
    if pgrep -f "mcp-server-chart" > /dev/null; then
        log_info "mcp-server-chart started successfully"
        log_info "  URL: http://localhost:1122/sse"
    else
        log_error "Failed to start mcp-server-chart"
        return 1
    fi
}

# MCP ECharts 시작 (포트 3033)
start_echarts_server() {
    log_info "Starting mcp-echarts on port 3033..."

    # 기존 프로세스 확인
    if pgrep -f "mcp-echarts" > /dev/null; then
        log_warn "mcp-echarts is already running"
        return 0
    fi

    # mcp-echarts가 설치되어 있는지 확인
    if ! command -v mcp-echarts &> /dev/null; then
        log_warn "mcp-echarts not found. Installing globally..."
        npm install -g mcp-echarts
    fi

    nohup mcp-echarts -t sse \
        > "$LOG_DIR/mcp-echarts.log" 2>&1 &

    sleep 2
    if pgrep -f "mcp-echarts" > /dev/null; then
        log_info "mcp-echarts started successfully"
        log_info "  URL: http://localhost:3033/sse"
    else
        log_error "Failed to start mcp-echarts"
        return 1
    fi
}

# 모든 서버 중지
stop_all() {
    log_info "Stopping all MCP servers..."

    pkill -f "mcp-server-chart" 2>/dev/null && log_info "Stopped mcp-server-chart" || true
    pkill -f "mcp-echarts" 2>/dev/null && log_info "Stopped mcp-echarts" || true

    log_info "All MCP servers stopped"
}

# 상태 확인
status() {
    echo "=== MCP Servers Status ==="
    echo ""

    if pgrep -f "mcp-server-chart" > /dev/null; then
        echo -e "@antv/mcp-server-chart: ${GREEN}RUNNING${NC} (http://localhost:1122/sse)"
    else
        echo -e "@antv/mcp-server-chart: ${RED}STOPPED${NC}"
    fi

    if pgrep -f "mcp-echarts" > /dev/null; then
        echo -e "mcp-echarts:            ${GREEN}RUNNING${NC} (http://localhost:3033/sse)"
    else
        echo -e "mcp-echarts:            ${RED}STOPPED${NC}"
    fi

    echo ""
}

# 메인 로직
case "${1:-all}" in
    all)
        log_info "Starting all MCP servers..."
        start_chart_server
        start_echarts_server
        echo ""
        status
        ;;
    chart)
        start_chart_server
        ;;
    echarts)
        start_echarts_server
        ;;
    stop)
        stop_all
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 [all|chart|echarts|stop|status]"
        echo ""
        echo "Commands:"
        echo "  all      - Start all MCP servers (default)"
        echo "  chart    - Start @antv/mcp-server-chart only"
        echo "  echarts  - Start mcp-echarts only"
        echo "  stop     - Stop all MCP servers"
        echo "  status   - Show server status"
        exit 1
        ;;
esac
