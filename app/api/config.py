#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置API
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()


@router.get("/all")
async def get_all_config(request: Request):
    """获取全部配置"""
    config = getattr(request.app.state, 'config', None)
    if config:
        return config.get_all()
    return {}


@router.get("/llm")
async def get_llm_config(request: Request):
    """获取大模型配置"""
    config = getattr(request.app.state, 'config', None)
    if config:
        return {
            "enabled": config.get("llm.enabled", False),
            "api_url": config.get("llm.api_url", ""),
            "api_key": config.get("llm.api_key", ""),
            "model": config.get("llm.model", "gpt-3.5-turbo"),
            "temperature": config.get("llm.temperature", 0.7),
            "system_prompt": config.get("llm.system_prompt", "")
        }
    return {}


@router.post("/llm")
async def save_llm_config(request: Request):
    """保存大模型配置"""
    config = getattr(request.app.state, 'config', None)
    data = await request.json()

    if config:
        config.set("llm.enabled", data.get("enabled", False))
        config.set("llm.api_url", data.get("api_url", ""))
        config.set("llm.api_key", data.get("api_key", ""))
        config.set("llm.model", data.get("model", "gpt-3.5-turbo"))
        config.set("llm.temperature", data.get("temperature", 0.7))
        config.set("llm.system_prompt", data.get("system_prompt", ""))
        config.save()

    return {"success": True}


@router.get("/ha")
async def get_ha_config(request: Request):
    """获取HA配置"""
    config = getattr(request.app.state, 'config', None)
    if config:
        return {
            "enabled": config.get("home_assistant.enabled", False),
            "url": config.get("home_assistant.url", ""),
            "token": config.get("home_assistant.token", ""),
            "auto_refresh": config.get("home_assistant.auto_refresh", True)
        }
    return {}


@router.post("/ha")
async def save_ha_config(request: Request):
    """保存HA配置"""
    config = getattr(request.app.state, 'config', None)
    data = await request.json()

    if config:
        config.set("home_assistant.enabled", data.get("enabled", False))
        config.set("home_assistant.url", data.get("url", ""))
        config.set("home_assistant.token", data.get("token", ""))
        config.set("home_assistant.auto_refresh", data.get("auto_refresh", True))
        config.save()

    return {"success": True}


@router.get("/music")
async def get_music_config(request: Request):
    """获取音乐配置"""
    config = getattr(request.app.state, 'config', None)
    if config:
        return {
            "enabled": config.get("music.enabled", False),
            "source": config.get("music.source", "netEase"),
            "local_api_url": config.get("music.local_api_url", "http://localhost:3000"),
            "logged_in": bool(config.get("music.cookie", ""))
        }
    return {}


@router.post("/music")
async def save_music_config(request: Request):
    """保存音乐配置"""
    config = getattr(request.app.state, 'config', None)
    data = await request.json()

    if config:
        config.set("music.enabled", data.get("enabled", False))
        config.set("music.source", data.get("source", "netEase"))
        config.set("music.local_api_url", data.get("local_api_url", "http://localhost:3000"))
        config.save()

    return {"success": True}


@router.post("/save")
async def save_all_config(request: Request):
    """保存配置"""
    config = getattr(request.app.state, 'config', None)
    if config:
        data = await request.json()
        for key, value in data.items():
            config.set(key, value)
        config.save()
        return {"success": True}
    return {"success": False}


@router.post("/reload")
async def reload_config(request: Request):
    """重载配置"""
    config = getattr(request.app.state, 'config', None)
    if config:
        config.load()
        return {"success": True}
    return {"success": False}
