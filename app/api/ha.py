#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Home Assistant API
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """获取HA状态"""
    config = getattr(request.app.state, 'config', None)
    ha = getattr(request.app.state, 'ha', None)

    if not config or not ha:
        return {"connected": False}

    # 测试连接
    connected = ha.test_connection()
    return {
        "connected": connected,
        "url": config.get("home_assistant.url", ""),
        "enabled": config.get("home_assistant.enabled", False)
    }


@router.get("/entities")
async def get_entities(request: Request, domain: str = None):
    """获取实体列表"""
    config = getattr(request.app.state, 'config', None)
    ha = getattr(request.app.state, 'ha', None)

    if not config or not ha:
        return {"entities": []}

    if not config.get("home_assistant.enabled", False):
        return {"entities": [], "message": "HA未启用"}

    try:
        if domain:
            entities = ha.get_entities(domain)
        else:
            entities = ha.get_entities()

        # 简化返回
        result = []
        for e in entities:
            result.append({
                "entity_id": e.get("entity_id", ""),
                "state": e.get("state", "unknown"),
                "friendly_name": e.get("attributes", {}).get("friendly_name", ""),
                "domain": e.get("entity_id", "").split(".")[0] if "." in e.get("entity_id", "") else "unknown"
            })

        return {"entities": result}
    except Exception as e:
        return {"entities": [], "error": str(e)}


@router.post("/control")
async def control(entity_id: str, action: str, request: Request):
    """控制设备"""
    config = getattr(request.app.state, 'config', None)
    ha = getattr(request.app.state, 'ha', None)

    if not config or not ha:
        raise HTTPException(status_code=500, detail="服务未初始化")

    if not config.get("home_assistant.enabled", False):
        raise HTTPException(status_code=400, detail="HA未启用")

    try:
        if action == "on":
            success, msg = ha.turn_on(entity_id)
        elif action == "off":
            success, msg = ha.turn_off(entity_id)
        elif action == "toggle":
            success, msg = ha.toggle(entity_id)
        else:
            raise HTTPException(status_code=400, detail="无效的操作")

        if success:
            return {"success": True, "message": f"{entity_id} 已{action}"}
        else:
            return {"success": False, "message": str(msg)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/states")
async def get_states(request: Request):
    """获取所有状态"""
    config = getattr(request.app.state, 'config', None)
    ha = getattr(request.app.state, 'ha', None)

    if not config or not ha:
        return {"states": []}

    if not config.get("home_assistant.enabled", False):
        return {"states": [], "message": "HA未启用"}

    try:
        states = ha.get_states()
        return {"states": states}
    except Exception as e:
        return {"states": [], "error": str(e)}


@router.get("/test")
async def test_connection(request: Request):
    """测试连接"""
    config = getattr(request.app.state, 'config', None)
    ha = getattr(request.app.state, 'ha', None)

    if not config or not ha:
        return {"success": False, "message": "服务未初始化"}

    try:
        success = ha.test_connection()
        if success:
            return {"success": True, "message": "连接成功"}
        else:
            return {"success": False, "message": "连接失败"}
    except Exception as e:
        return {"success": False, "message": str(e)}
