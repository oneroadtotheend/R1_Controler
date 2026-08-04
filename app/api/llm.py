#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型API
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """获取LLM状态"""
    config = getattr(request.app.state, 'config', None)
    enabled = config.get("llm.enabled", False) if config else False
    return {"enabled": enabled}


@router.post("/chat")
async def chat(request: Request):
    """聊天"""
    config = getattr(request.app.state, 'config', None)
    llm = getattr(request.app.state, 'llm', None)

    if not config or not llm:
        raise HTTPException(status_code=500, detail="服务未初始化")

    data = await request.json()
    message = data.get("message", "")

    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 检查是否启用
    if not config.get("llm.enabled", False):
        return {
            "response": "大模型服务未启用，请在设置中配置并启用。",
            "requires_config": True
        }

    # 检查API配置
    api_key = config.get("llm.api_key", "")
    if not api_key:
        return {
            "response": "请先在设置中配置API Key",
            "requires_config": True
        }

    try:
        # 意图识别 + 天气服务
        message_lower = message.lower()
        weather_keywords = ["天气", "温度", "气候", "晴", "雨", "雪", "风"]
        is_weather_query = any(kw in message for kw in weather_keywords)

        if is_weather_query:
            # 调用天气服务
            from modules.weather_service import get_weather_service
            weather_svc = get_weather_service()

            # 尝试从消息中提取城市名
            city = None
            # 简单的城市提取逻辑
            city_keywords = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆", "武汉", "西安", "苏州", "天津"]
            for ck in city_keywords:
                if ck in message:
                    city = ck
                    break

            # 获取客户端 IP
            client_ip = request.client.host if request.client else None

            # 如果没有指定城市，通过 IP 自动定位
            response = weather_svc.get_weather(city=city, ip=client_ip)
        else:
            response = llm.chat(message)

        return {"response": response}
    except Exception as e:
        return {"response": f"调用失败: {str(e)}", "error": True}


@router.post("/intent")
async def analyze_intent(request: Request):
    """意图分析"""
    config = getattr(request.app.state, 'config', None)
    llm = getattr(request.app.state, 'llm', None)

    if not config or not llm:
        raise HTTPException(status_code=500, detail="服务未初始化")

    data = await request.json()
    message = data.get("message", "")

    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    if not config.get("llm.enabled", False):
        return {"intent": "chat", "message": message}

    try:
        result = llm.analyze_intent(message)
        return result
    except Exception as e:
        return {"intent": "chat", "message": message, "error": str(e)}


@router.post("/test")
async def test_api(request: Request):
    """测试API"""
    config = getattr(request.app.state, 'config', None)
    llm = getattr(request.app.state, 'llm', None)

    if not config or not llm:
        raise HTTPException(status_code=500, detail="服务未初始化")

    data = await request.json()
    message = data.get("message", "你好")

    # 临时测试
    api_url = data.get("api_url", config.get("llm.api_url", ""))
    api_key = data.get("api_key", config.get("llm.api_key", ""))
    model = data.get("model", config.get("llm.model", "gpt-3.5-turbo"))

    if not api_key:
        return {"success": False, "message": "请提供API Key"}

    # 临时设置
    config.set("llm.api_url", api_url)
    config.set("llm.api_key", api_key)
    config.set("llm.model", model)
    config.set("llm.enabled", True)

    try:
        response = llm.chat(message)
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "message": str(e)}
