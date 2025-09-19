#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import json
import os
import requests

# 模拟延时 0.5 秒
time.sleep(0.5)

# 配置 OpenAI API 地址和 Key
api_url = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('MODEL', 'gpt-4o-mini')
debug = os.getenv('DEBUG', 'false').lower() in ['true', '1', 'yes']
use_ollama = os.getenv('USE_OLLAMA', 'false').lower() in ['true', '1', 'yes']


if not api_key:
    raise ValueError("API key not found! Please set the OPENAI_API_KEY environment variable.")

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

    prompt = f"Translate the following text to {target_language} and just response translation text(If it's just a single word, please also provide the english pronunciation().), content below:\n\n{text}"

    data = {
        "model": model,
        "messages": [{"role": "system", "content": "You are a professional translator, and the content I need translated should prioritize terminology related to the field of computer technology."},
                     {"role": "user", "content": prompt}],
        "max_tokens": 1000,
    }

    if debug:
        print(f"Debug - 请求URL: {api_url}")
        print(f"Debug - 请求头: {headers}")
        print(f"Debug - 请求体: {json.dumps(data, ensure_ascii=False)}")

    response = requests.post(api_url, headers=headers, json=data)

    if debug:
        print(f"Debug - 响应状态码: {response.status_code}")
        print(f"Debug - 响应内容: {response.text}")

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

    if not query:
        # 如果没有输入内容，返回空结果
        print(json.dumps({"items": []}))
        return

    # 判断输入语言是否为中文（通过 Unicode 范围判断）
    if any('\u4e00' <= char <= '\u9fff' for char in query):
        # 如果输入是中文，翻译为英文
        translated = translate_text(query, target_language="en")
    else:
        # 如果输入是英文，翻译为中文
        translated = translate_text(query, target_language="zh")

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
