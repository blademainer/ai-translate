#!/bin/bash
# AI翻译脚本标准测试工具
# 用于验证openai.py脚本的长文本翻译功能

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试配置
SCRIPT_PATH="./openai.py"
OLLAMA_URL="http://localhost:11434"
DEFAULT_MODEL="qwen2.5:7b"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖环境..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查脚本文件
    if [ ! -f "$SCRIPT_PATH" ]; then
        print_error "翻译脚本 $SCRIPT_PATH 不存在"
        exit 1
    fi
    
    # 检查Ollama服务
    if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        print_error "Ollama服务未运行，请启动Ollama服务"
        print_info "启动命令: ollama serve"
        exit 1
    fi
    
    # 检查模型是否可用
    if ! ollama list | grep -q "$DEFAULT_MODEL"; then
        print_warning "模型 $DEFAULT_MODEL 未安装"
        print_info "正在下载模型: $DEFAULT_MODEL"
        ollama pull "$DEFAULT_MODEL"
    fi
    
    print_success "依赖检查完成"
}

# 设置测试环境
setup_test_env() {
    print_info "设置测试环境..."
    
    export USE_OLLAMA=true
    export OPENAI_API_URL="$OLLAMA_URL/api/chat"
    export OPENAI_API_KEY="ollama"
    export MODEL="$DEFAULT_MODEL"
    export DEBUG=true
    export DEBUG_VERBOSE=false
    export LONG_TEXT_THRESHOLD=100
    export MAX_SEGMENT_LENGTH=300
    export USE_TURBO=true
    
    print_success "测试环境设置完成"
    print_info "使用模型: $MODEL"
    print_info "API地址: $OPENAI_API_URL"
}

# 测试短文本翻译
test_short_text() {
    print_info "测试短文本翻译..."
    
    local short_text="Hello AI"
    local result
    
    print_info "测试文本: $short_text"
    
    if result=$(/usr/bin/python3 "$SCRIPT_PATH" "$short_text" 2>&1); then
        if echo "$result" | grep -q "items"; then
            print_success "短文本翻译测试通过"
            return 0
        else
            print_error "短文本翻译返回格式错误"
            echo "$result"
            return 1
        fi
    else
        print_error "短文本翻译失败"
        echo "$result"
        return 1
    fi
}

# 测试缩略词发音
test_acronym_pronunciation() {
    print_info "测试缩略词发音..."
    
    local acronyms=("CAP" "API" "CPU" "GPU" "SQL")
    local failed_count=0
    
    for acronym in "${acronyms[@]}"; do
        print_info "测试缩略词: $acronym"
        local result
        
        if result=$(/usr/bin/python3 "$SCRIPT_PATH" "$acronym" 2>&1); then
            # 检查是否包含正确的字母发音格式，而不是汉语拼音
            if echo "$result" | grep -q "items"; then
                local translation_content=$(echo "$result" | /usr/bin/python3 -c "import sys, json; data=json.load(sys.stdin); print(data['items'][0]['title'])")
                
                # 检查是否包含字母发音（包含斜杠或音标符号）
                if echo "$translation_content" | grep -qE '(/[a-zA-Z\s]+/|[ɪəɑɒʌʊiːuːaɪaʊ]+)'; then
                    print_success "$acronym 发音测试通过: $translation_content"
                else
                    print_warning "$acronym 可能缺少正确的发音标注: $translation_content"
                fi
            else
                print_error "$acronym 翻译返回格式错误"
                echo "$result"
                ((failed_count++))
            fi
        else
            print_error "$acronym 翻译失败"
            echo "$result"
            ((failed_count++))
        fi
    done
    
    if [ $failed_count -eq 0 ]; then
        print_success "缩略词发音测试全部通过"
        return 0
    else
        print_error "缩略词发音测试失败: $failed_count/${#acronyms[@]}"
        return 1
    fi
}

# 测试中文长文本翻译
test_chinese_long_text() {
    print_info "测试中文长文本翻译..."
    
    local chinese_text="人工智能技术正在快速发展，它已经成为现代科技领域的重要组成部分。机器学习作为人工智能的核心技术之一，通过算法让计算机从数据中学习模式，从而实现智能化的决策和预测。深度学习进一步推动了这一领域的发展！它使用多层神经网络来模拟人脑的工作方式，在图像识别、语音处理和自然语言理解等方面取得了突破性进展？"
    
    print_info "测试中文长文本 (${#chinese_text} 字符)"
    
    local result
    if result=$(/usr/bin/python3 "$SCRIPT_PATH" "$chinese_text" 2>&1); then
        if echo "$result" | grep -q "检测到长文本"; then
            print_success "中文长文本检测正常"
        else
            print_warning "未检测到长文本标志"
        fi
        
        if echo "$result" | grep -q "items"; then
            print_success "中文长文本翻译测试通过"
            return 0
        else
            print_error "中文长文本翻译返回格式错误"
            echo "$result"
            return 1
        fi
    else
        print_error "中文长文本翻译超时或失败"
        echo "$result"
        return 1
    fi
}

# 测试英文长文本翻译
test_english_long_text() {
    print_info "测试英文长文本翻译..."
    
    local english_text="Machine learning algorithms enable computers to learn from vast amounts of data without being explicitly programmed for every task. This capability has revolutionized industries ranging from healthcare to finance. Deep learning, a subset of machine learning, uses neural networks with multiple layers to process information in ways that mimic human brain function. These systems have achieved remarkable success in computer vision, natural language processing, and speech recognition."
    
    print_info "测试英文长文本 (${#english_text} 字符)"
    
    local result
    if result=$(/usr/bin/python3 "$SCRIPT_PATH" "$english_text" 2>&1); then
        if echo "$result" | grep -q "检测到长文本"; then
            print_success "英文长文本检测正常"
        else
            print_warning "未检测到长文本标志"
        fi
        
        if echo "$result" | grep -q "分为.*段进行翻译"; then
            print_success "英文长文本分段正常"
        fi
        
        if echo "$result" | grep -q "items"; then
            print_success "英文长文本翻译测试通过"
            return 0
        else
            print_error "英文长文本翻译返回格式错误"
            echo "$result"
            return 1
        fi
    else
        print_error "英文长文本翻译超时或失败"
        echo "$result"
        return 1
    fi
}

# 测试HTTP调试功能
test_http_debug() {
    print_info "测试HTTP调试功能..."
    
    local test_text="Debug test"
    local result
    
    # 测试HTTP调试信息输出
    if result=$(/usr/bin/python3 "$SCRIPT_PATH" "$test_text" 2>&1); then
        if echo "$result" | grep -q "HTTP请求详情"; then
            print_success "HTTP请求调试信息正常"
        else
            print_warning "未检测到HTTP请求调试信息"
        fi
        
        if echo "$result" | grep -q "Request Body"; then
            print_success "请求体参数调试信息正常"
        fi
        
        if echo "$result" | grep -q "HTTP响应详情"; then
            print_success "HTTP响应调试信息正常"
        fi
        
        if echo "$result" | grep -q "Status Code"; then
            print_success "响应状态码调试信息正常"
        fi
        
        if echo "$result" | grep -q "items"; then
            print_success "HTTP调试模式翻译测试通过"
            return 0
        else
            print_error "HTTP调试模式翻译返回格式错误"
            echo "$result"
            return 1
        fi
    else
        print_error "HTTP调试测试失败"
        echo "$result"
        return 1
    fi
}

# 测试Turbo模式功能
test_turbo_mode() {
    print_info "测试Turbo模式功能..."
    
    local test_text="Machine learning and artificial intelligence"
    local result
    
    # 测试turbo模式状态检测
    if result=$(/usr/bin/python3 "$SCRIPT_PATH" "$test_text" 2>&1); then
        if echo "$result" | grep -q "Turbo模式状态: 启用"; then
            print_success "Turbo模式检测正常"
        else
            print_warning "未检测到Turbo模式启用标志"
            echo "$result" | grep "Turbo模式状态" || print_info "Debug信息中无Turbo状态"
        fi
        
        if echo "$result" | grep -q "性能优化"; then
            print_success "Turbo模式性能优化配置正常"
        fi
        
        if echo "$result" | grep -q "items"; then
            print_success "Turbo模式翻译测试通过"
            return 0
        else
            print_error "Turbo模式翻译返回格式错误"
            echo "$result"
            return 1
        fi
    else
        print_error "Turbo模式测试失败"
        echo "$result"
        return 1
    fi
}

# 性能测试
test_performance() {
    print_info "进行性能测试..."
    
    local test_text="Artificial Intelligence is transforming technology."
    local start_time
    local end_time
    local duration
    
    start_time=$(date +%s)
    /usr/bin/python3 "$SCRIPT_PATH" "$test_text" > /dev/null 2>&1
    end_time=$(date +%s)
    
    duration=$((end_time - start_time))
    
    if [ $duration -lt 30 ]; then
        print_success "性能测试通过 (${duration}秒)"
    else
        print_warning "翻译耗时较长 (${duration}秒)"
    fi
}

# 清理测试环境
cleanup() {
    print_info "清理测试环境..."
    unset USE_OLLAMA OPENAI_API_URL OPENAI_API_KEY MODEL DEBUG DEBUG_VERBOSE LONG_TEXT_THRESHOLD MAX_SEGMENT_LENGTH USE_TURBO
    print_success "清理完成"
}

# 显示帮助信息
show_help() {
    echo "AI翻译脚本测试工具"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -s, --short    仅测试短文本"
    echo "  -l, --long     仅测试长文本"
    echo "  -a, --acronym  仅测试缩略词发音"
    echo "  -t, --turbo    仅测试Turbo模式"
    echo "  -d, --debug    仅测试HTTP调试功能"
    echo "  -p, --perf     仅进行性能测试"
    echo "  -m, --model    指定测试模型 (默认: $DEFAULT_MODEL)"
    echo ""
    echo "示例:"
    echo "  $0                    # 运行所有测试"
    echo "  $0 -s                 # 仅测试短文本"
    echo "  $0 -a                 # 仅测试缩略词发音"
    echo "  $0 -t                 # 仅测试Turbo模式"
    echo "  $0 -d                 # 仅测试HTTP调试功能"
    echo "  $0 -m qwen:32b        # 使用指定模型测试"
}

# 主测试函数
run_tests() {
    local test_short=true
    local test_long=true
    local test_acronym=true
    local test_turbo=true
    local test_debug=true
    local test_perf=true
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--short)
                test_long=false
                test_acronym=false
                test_turbo=false
                test_debug=false
                test_perf=false
                shift
                ;;
            -l|--long)
                test_short=false
                test_acronym=false
                test_turbo=false
                test_debug=false
                test_perf=false
                shift
                ;;
            -a|--acronym)
                test_short=false
                test_long=false
                test_turbo=false
                test_debug=false
                test_perf=false
                shift
                ;;
            -t|--turbo)
                test_short=false
                test_long=false
                test_acronym=false
                test_debug=false
                test_perf=false
                shift
                ;;
            -d|--debug)
                test_short=false
                test_long=false
                test_acronym=false
                test_turbo=false
                test_perf=false
                shift
                ;;
            -p|--perf)
                test_short=false
                test_long=false
                test_acronym=false
                test_turbo=false
                test_debug=false
                shift
                ;;
            -m|--model)
                DEFAULT_MODEL="$2"
                shift 2
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_info "开始AI翻译脚本测试"
    echo "================================"
    
    # 检查依赖和设置环境
    check_dependencies
    setup_test_env
    
    local failed_tests=0
    local total_tests=0
    
    # 运行测试
    if [ "$test_short" = true ]; then
        ((total_tests++))
        if ! test_short_text; then
            ((failed_tests++))
        fi
        echo ""
    fi
    
    if [ "$test_acronym" = true ]; then
        ((total_tests++))
        if ! test_acronym_pronunciation; then
            ((failed_tests++))
        fi
        echo ""
    fi
    
    if [ "$test_turbo" = true ]; then
        ((total_tests++))
        if ! test_turbo_mode; then
            ((failed_tests++))
        fi
        echo ""
    fi
    
    if [ "$test_debug" = true ]; then
        ((total_tests++))
        if ! test_http_debug; then
            ((failed_tests++))
        fi
        echo ""
    fi
    
    if [ "$test_long" = true ]; then
        ((total_tests+=2))
        if ! test_chinese_long_text; then
            ((failed_tests++))
        fi
        echo ""
        
        if ! test_english_long_text; then
            ((failed_tests++))
        fi
        echo ""
    fi
    
    if [ "$test_perf" = true ]; then
        ((total_tests++))
        if ! test_performance; then
            ((failed_tests++))
        fi
        echo ""
    fi
    
    # 清理环境
    cleanup
    
    # 显示测试结果
    echo "================================"
    if [ $failed_tests -eq 0 ]; then
        print_success "所有测试通过! ($total_tests/$total_tests)"
        exit 0
    else
        print_error "测试失败: $failed_tests/$total_tests"
        exit 1
    fi
}

# 脚本入口
main() {
    # 捕获中断信号，确保清理
    trap cleanup EXIT INT TERM
    
    run_tests "$@"
}

# 如果直接运行此脚本，则执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
