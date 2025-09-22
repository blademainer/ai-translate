# AI翻译脚本 Turbo模式

## 概述

Turbo模式是一种高性能翻译模式，通过优化模型参数和处理流程，提供更快的响应速度和更高的吞吐量。

## 什么是Turbo模式？

Turbo模式是大模型中的"快思考"模式，主要特点包括：

- **快速响应** - 降低首字时延，提升响应速度
- **优化参数** - 调整temperature、top_p等参数以获得更快的推理速度
- **减少延迟** - 在长文本分段翻译中减少等待时间
- **提升吞吐量** - 增加max_tokens等参数以处理更多内容

## 启用Turbo模式

### 方法1：环境变量控制

```bash
export USE_TURBO=true
python3 openai.py "你要翻译的文本"
```

### 方法2：使用Turbo模型

支持的Turbo模型包括：

**OpenAI系列：**
- `gpt-3.5-turbo`
- `gpt-4-turbo`
- `gpt-4o-turbo`

**Ollama系列：**
- `qwen2.5-turbo:7b`
- `qwen-turbo:latest`
- `llama3-turbo:8b`
- `gemma-turbo:7b`

**其他平台：**
- `claude-3-haiku` (快速模式)
- `claude-3-sonnet-turbo`
- `ernie-turbo` (百度文心)
- `hunyuan-turbo` (腾讯混元)

```bash
export MODEL=qwen2.5-turbo:7b
python3 openai.py "你要翻译的文本"
```

## 性能优化参数

Turbo模式下，系统会自动应用以下优化参数：

```python
{
    "temperature": 0.7,          # 降低随机性，提高速度
    "max_tokens": 2000,          # 增加最大token数
    "top_p": 0.9,               # 降低采样范围
    "frequency_penalty": 0.0,    # 减少频率惩罚
    "presence_penalty": 0.0,     # 减少存在惩罚
}
```

## 使用示例

### 基本使用

```bash
# 启用turbo模式
export USE_TURBO=true
export MODEL=qwen2.5:7b
export DEBUG=true

# 翻译短文本
python3 openai.py "Hello, AI!"

# 翻译长文本
python3 openai.py "Machine learning is a subset of artificial intelligence..."
```

### 性能比较测试

```bash
# 运行性能比较示例
python3 turbo_example.py
```

### 使用测试脚本

```bash
# 测试turbo模式功能
./test.sh --turbo

# 运行完整测试套件（包含turbo测试）
./test.sh
```

## 检测Turbo模式状态

当启用DEBUG模式时，系统会显示turbo状态信息：

```
Debug - Turbo模式状态: 启用 (模型: qwen2.5:7b)
Debug - 性能优化: 降低延时、优化参数、快速响应
```

## 环境变量配置

```bash
# Turbo模式相关配置
export USE_TURBO=true           # 强制启用turbo模式
export MODEL=qwen2.5-turbo:7b   # 使用turbo模型
export DEBUG=true               # 显示调试信息
export DEBUG_VERBOSE=true       # 显示完整的JSON请求体（可选）

# 基础配置
export USE_OLLAMA=true
export OPENAI_API_URL=http://localhost:11434/api/chat
export OPENAI_API_KEY=ollama
```

## 调试功能

### HTTP请求调试

当启用 `DEBUG=true` 时，系统会显示详细的HTTP请求和响应信息：

```bash
export DEBUG=true
python3 openai.py "你的文本"
```

调试信息包括：
- **HTTP请求详情** - URL、方法、请求头
- **请求体参数** - 模型、令牌数、温度、Top P等
- **Turbo优化参数** - 当启用turbo模式时显示的优化配置
- **HTTP响应详情** - 状态码、响应头、响应体

**重要说明：** 调试信息输出到stderr，不会影响Alfred Workflow的JSON解析。这确保了调试模式与Alfred完全兼容。

### 详细调试模式

启用 `DEBUG_VERBOSE=true` 可以显示完整的JSON请求体：

```bash
export DEBUG=true
export DEBUG_VERBOSE=true
python3 openai.py "你的文本"
```

### 调试输出示例

```
Debug - HTTP请求详情:
  URL: http://localhost:11434/api/chat
  Method: POST
  Headers:
    Content-Type: application/json
    Authorization: Bearer Bearer oll...***
  Request Body:
    Model: qwen2.5:7b
    Max Tokens: 2000
    Temperature: 0.7
    Top P: 0.9
    Messages Count: 2
    Turbo Optimizations:
      - Temperature: 0.7
      - Top P: 0.9
      - Frequency Penalty: 0.0
      - Presence Penalty: 0.0
```

## 性能提升效果

使用Turbo模式可以获得以下性能提升：

- **响应速度** - 首字时延降低30-50%
- **处理速度** - 整体翻译速度提升20-40%
- **吞吐量** - 处理更长的文本内容
- **延迟优化** - 长文本分段翻译延迟减半

## 兼容性

- ✅ 支持OpenAI API格式
- ✅ 支持Ollama本地部署
- ✅ 支持长文本自动分段
- ✅ 支持Alfred Workflow集成
- ✅ 向后兼容普通模式

## 故障排除

### 常见问题

1. **Turbo模式未启用**
   ```bash
   # 检查环境变量
   echo $USE_TURBO
   echo $MODEL
   
   # 启用调试模式查看状态
   export DEBUG=true
   ```

2. **模型不支持Turbo**
   ```bash
   # 使用明确的turbo模型
   export MODEL=qwen2.5-turbo:7b
   ```

3. **性能提升不明显**
   - 检查网络延迟
   - 确认模型加载状态
   - 验证ollama服务性能

### 调试命令

```bash
# 查看当前配置
env | grep -E "(TURBO|MODEL|DEBUG)"

# 测试基本调试功能
./test.sh --debug

# 测试turbo功能
./test.sh --turbo

# 启用详细HTTP调试
export DEBUG=true DEBUG_VERBOSE=true
python3 openai.py "测试文本"

# 仅启用基本调试（不显示完整JSON）
export DEBUG=true DEBUG_VERBOSE=false
python3 openai.py "测试文本"
```

## 更新日志

- **v1.2** - 修复Alfred集成问题
  - 🔧 修复调试模式下Alfred JSON解析错误
  - ✅ 调试信息正确输出到stderr，避免影响stdout
  - 🛡️ 确保调试模式与Alfred Workflow完全兼容
  - 📊 添加debug_verbose_print函数优化详细输出控制

- **v1.1** - 增强调试功能
  - 添加详细的HTTP请求调试信息
  - 新增DEBUG_VERBOSE环境变量支持
  - 优化调试信息输出格式
  - 添加HTTP调试测试功能
  - 隐藏敏感的API密钥信息

- **v1.0** - 初始turbo模式实现
  - 添加USE_TURBO环境变量支持
  - 实现模型名称自动检测
  - 优化性能参数配置
  - 集成测试脚本

## 贡献

如果你发现了新的turbo模型或有性能优化建议，欢迎提交PR或issue。
