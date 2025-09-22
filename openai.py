#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import json
import os
import requests
import re

# 模拟延时 0.5 秒
time.sleep(0.5)

# 配置 OpenAI API 地址和 Key
api_url = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('MODEL', 'gpt-4o-mini')
debug = os.getenv('DEBUG', 'false').lower() in ['true', '1', 'yes']
use_ollama = os.getenv('USE_OLLAMA', 'false').lower() in ['true', '1', 'yes']
# Turbo模式配置
use_turbo = os.getenv('USE_TURBO', 'false').lower() in ['true', '1', 'yes']
# Debug详细模式配置 - 显示完整的JSON请求体
debug_verbose = os.getenv('DEBUG_VERBOSE', 'false').lower() in ['true', '1', 'yes']
# 长文本检测阈值
long_text_threshold = int(os.getenv('LONG_TEXT_THRESHOLD', '100'))  # 默认100字符
max_segment_length = int(os.getenv('MAX_SEGMENT_LENGTH', '400'))    # 每段最大长度


if not api_key:
    raise ValueError("API key not found! Please set the OPENAI_API_KEY environment variable.")

def is_turbo_model(model_name):
    """
    检测模型是否支持turbo模式
    """
    turbo_models = [
        # OpenAI turbo模型
        'gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4o-turbo',
        # 其他支持turbo的模型
        'claude-3-haiku', 'claude-3-sonnet-turbo',
        # Ollama中的turbo模型
        'qwen2.5-turbo', 'qwen-turbo', 'llama3-turbo', 'gemma-turbo',
        # 百度文心turbo
        'ernie-turbo', 'ernie-speed',
        # 腾讯混元turbo
        'hunyuan-turbo'
    ]
    
    model_lower = model_name.lower()
    return any(turbo_keyword in model_lower for turbo_keyword in ['turbo', 'speed', 'fast'])

def get_turbo_optimized_params(base_params):
    """
    获取turbo模式优化的参数
    """
    turbo_params = base_params.copy()
    
    if use_turbo or is_turbo_model(model):
        # Turbo模式优化参数
        turbo_params.update({
            "temperature": 0.7,  # 降低随机性，提高响应速度
            "max_tokens": 2000,  # 增加最大token数
            "top_p": 0.9,       # 降低采样范围，提高响应速度
            "frequency_penalty": 0.0,  # 减少频率惩罚
            "presence_penalty": 0.0,   # 减少存在惩罚
        })
        
        # 如果是流式API，启用流式模式
        if use_ollama:
            turbo_params["stream"] = False  # Ollama默认不使用stream以提高兼容性
        
        if debug:
            print(f"Debug - 启用Turbo模式优化，模型: {model}")
    
    return turbo_params

def is_long_text(text):
    """
    检测是否为长文本
    判断标准：
    1. 文本长度超过阈值，且
    2. 包含多个句子分隔符（中文句号、分号、换行符等）
    """
    # 检测中文分隔符的数量
    chinese_separators = ['。', '；', '？', '！', '\n']
    separator_count = sum(text.count(sep) for sep in chinese_separators)
    
    # 检测英文分隔符的数量
    english_separators = ['. ', '; ', '? ', '! ', '\n']
    separator_count += sum(text.count(sep) for sep in english_separators)
    
    # 如果文本长度超过阈值且包含2个或以上分隔符，则认为是长文本
    return len(text) >= long_text_threshold and separator_count >= 2

def segment_text(text):
    """
    将长文本分段
    优先级：句号 > 分号 > 问号/感叹号 > 换行符
    """
    segments = []
    
    # 定义分隔符优先级（按重要性排序）
    separators = [
        # 中文分隔符
        '。', '；', '？', '！',
        # 英文分隔符
        '. ', '; ', '? ', '! ',
        # 换行符
        '\n'
    ]
    
    current_text = text.strip()
    
    while current_text:
        if len(current_text) <= max_segment_length:
            # 如果剩余文本长度小于最大段落长度，直接作为一段
            segments.append(current_text.strip())
            break
        
        # 寻找最佳分割点
        best_split_pos = -1
        best_separator = None
        
        for separator in separators:
            # 在最大长度范围内寻找分隔符
            search_text = current_text[:max_segment_length]
            pos = search_text.rfind(separator)
            
            if pos > best_split_pos:
                best_split_pos = pos
                best_separator = separator
        
        if best_split_pos > 0:
            # 找到合适的分割点
            segment = current_text[:best_split_pos + len(best_separator)].strip()
            if segment:
                segments.append(segment)
            current_text = current_text[best_split_pos + len(best_separator):].strip()
        else:
            # 没有找到合适的分割点，强制按最大长度分割
            segment = current_text[:max_segment_length].strip()
            if segment:
                segments.append(segment)
            current_text = current_text[max_segment_length:].strip()
    
    return [seg for seg in segments if seg.strip()]

def translate_long_text(text, target_language="zh"):
    """
    翻译长文本，自动分段处理
    """
    if not is_long_text(text):
        # 如果不是长文本，直接调用普通翻译
        return translate_text(text, target_language)
    
    if debug:
        print(f"Debug - 检测到长文本，长度: {len(text)} 字符")
    
    # 分段处理
    segments = segment_text(text)
    
    if debug:
        print(f"Debug - 分为 {len(segments)} 段进行翻译")
        for i, segment in enumerate(segments, 1):
            print(f"Debug - 第{i}段 ({len(segment)}字符): {segment[:50]}...")
    
    translated_segments = []
    
    for i, segment in enumerate(segments, 1):
        if debug:
            print(f"Debug - 正在翻译第 {i}/{len(segments)} 段...")
        
        try:
            translated_segment = translate_text(segment, target_language)
            translated_segments.append(translated_segment)
            
            # 在分段翻译之间添加小延时，避免API限制
            # Turbo模式下减少延时
            if i < len(segments):
                delay = 0.1 if (use_turbo or is_turbo_model(model)) else 0.2
                time.sleep(delay)
                
        except Exception as e:
            if debug:
                print(f"Debug - 第{i}段翻译失败: {str(e)}")
            translated_segments.append(f"[翻译失败: {str(e)}]")
    
    # 拼接结果
    # 如果原文包含换行符，保持换行格式；否则用空格连接
    if '\n' in text:
        result = '\n'.join(translated_segments)
    else:
        result = ' '.join(translated_segments)
    
    if debug:
        print(f"Debug - 长文本翻译完成，结果长度: {len(result)} 字符")
    
    return result

def translate_text(text, target_language="zh"):
    """
    使用 OpenAI API 实现翻译功能。
    text：待翻译的文本
    target_language：目标语言，默认为中文（'zh'）
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    prompt = f"Translate the following text to {target_language} and just response translation text(If it's just a single word, please also provide the english pronunciation(). For acronyms like API, CAP, CPU, etc., use letter-by-letter pronunciation, e.g., CAP should be pronounced as /siː eɪ piː/, not as Chinese pinyin.), content below:\n\n{text}"

    # 基础参数
    base_data = {
        "model": model,
        "messages": [{"role": "system", "content": "You are a professional translator, and the content I need translated should prioritize terminology related to the field of computer technology."},
                     {"role": "user", "content": prompt}],
        "max_tokens": 1500,
    }
    
    # 应用turbo模式优化
    data = get_turbo_optimized_params(base_data)

    if debug:
        print(f"Debug - HTTP请求详情:")
        print(f"  URL: {api_url}")
        print(f"  Method: POST")
        print(f"  Headers:")
        for key, value in headers.items():
            # 隐藏敏感信息
            if key.lower() == 'authorization':
                print(f"    {key}: Bearer {value[:10]}...{value[-4:] if len(value) > 14 else '***'}")
            else:
                print(f"    {key}: {value}")
        
        print(f"  Request Body:")
        print(f"    Model: {data.get('model', 'N/A')}")
        print(f"    Max Tokens: {data.get('max_tokens', 'N/A')}")
        print(f"    Temperature: {data.get('temperature', 'N/A')}")
        print(f"    Top P: {data.get('top_p', 'N/A')}")
        print(f"    Messages Count: {len(data.get('messages', []))}")
        
        # 如果启用了turbo模式，显示优化参数
        if use_turbo or is_turbo_model(model):
            print(f"    Turbo Optimizations:")
            print(f"      - Temperature: {data.get('temperature', 'default')}")
            print(f"      - Top P: {data.get('top_p', 'default')}")
            print(f"      - Frequency Penalty: {data.get('frequency_penalty', 'default')}")
            print(f"      - Presence Penalty: {data.get('presence_penalty', 'default')}")
        
        # 显示完整的JSON请求体（可选择性显示）
        if debug_verbose:
            print(f"  Full JSON Body: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        print(f"Debug - 发送HTTP请求到 {'Ollama' if use_ollama else 'OpenAI API'}...")

    response = requests.post(api_url, headers=headers, json=data)

    if debug:
        print(f"Debug - HTTP响应详情:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Headers:")
        for key, value in response.headers.items():
            print(f"    {key}: {value}")
        
        # 限制响应内容的输出长度，避免过长
        response_text = response.text
        if len(response_text) > 1000:
            print(f"  Response Body (truncated): {response_text[:500]}...{response_text[-200:]}")
        else:
            print(f"  Response Body: {response_text}")
        
        print(f"  Response Size: {len(response_text)} characters")

    if response.status_code == 200:
        if use_ollama:
            # Ollama 返回的是流式响应，每行一个JSON
            # 我们从最后一个完整对象中提取内容
            try:
                full_content = ""
                for line in response.text.strip().split('\n'):
                    try:
                        line_data = json.loads(line)
                        if 'message' in line_data and 'content' in line_data['message']:
                            full_content += line_data['message']['content']
                    except json.JSONDecodeError:
                        if debug:
                            print(f"Debug - 无法解析JSON行: {line}")
                            
                return full_content.strip()
            except Exception as e:
                if debug:
                    print(f"Debug - Ollama解析错误: {str(e)}")
                return f"Error parsing Ollama response: {str(e)}"
        else:
            # 标准OpenAI API响应
            result = response.json()
            translation = result['choices'][0]['message']['content']
            return translation.strip()
    else:
        return f"Error: {response.status_code} - {response.text}"

def main():
    query = ' '.join(sys.argv[1:]).strip()

    # 显示turbo模式状态
    if debug:
        turbo_enabled = use_turbo or is_turbo_model(model)
        print(f"Debug - Turbo模式状态: {'启用' if turbo_enabled else '禁用'} (模型: {model})")
        if turbo_enabled:
            print("Debug - 性能优化: 降低延时、优化参数、快速响应")

    if not query:
        # 如果没有输入内容，返回空结果
        print(json.dumps({"items": []}))
        return

    # 判断输入语言是否为中文（通过 Unicode 范围判断）
    if any('\u4e00' <= char <= '\u9fff' for char in query):
        # 如果输入是中文，翻译为英文
        translated = translate_long_text(query, target_language="en")
    else:
        # 如果输入是英文，翻译为中文
        translated = translate_long_text(query, target_language="zh")

    # 返回翻译结果
    output = {
        "items": [
            {
                "title": translated,
                "subtitle": "按回车复制翻译结果",
                "arg": translated,
                "icon": {
                    "path": "icon.png"  # 可以自定义图标路径
                }
            }
        ]
    }
    
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
