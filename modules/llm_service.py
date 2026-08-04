#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型服务
"""

import requests
import json
import re


class LLMService:
    """大模型服务类"""

    def __init__(self, config):
        self.config = config

    def chat(self, message, history=None):
        """发送聊天"""
        api_url = self.config.get("llm.api_url")
        api_key = self.config.get("llm.api_key")
        model = self.config.get("llm.model")
        temperature = self.config.get("llm.temperature", 0.7)
        system_prompt = self.config.get("llm.system_prompt")

        if not api_key:
            raise Exception("请先配置API Key")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            for role, content in history[-10:]:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000
        }

        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.text}")

        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        raise Exception("API返回格式异常")

    def is_configured(self):
        """检查是否已配置"""
        api_key = self.config.get("llm.api_key")
        return bool(api_key)

    def analyze_intent(self, message):
        """意图分析"""
        prompt = f"""分析用户消息意图，返回JSON格式。

用户消息: {message}

意图类型:
- music_play: 播放音乐
- music_search: 搜索音乐
- device_control: 设备控制
- home_assistant: 智能家居
- chat: 对话
- query_info: 查询信息

返回格式:
{{"intent": "类型", "entities": {{}}, "confidence": 0.95}}
只返回JSON。"""

        try:
            result = self.chat(prompt)
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"intent": "chat", "confidence": 0.5}
        except:
            return {"intent": "chat", "confidence": 0.3}
