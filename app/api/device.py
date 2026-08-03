#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备控制API
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import base64
import os

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """获取设备状态"""
    adb = getattr(request.app.state, 'adb', None)
    if adb and adb.device_ip:
        info = adb.get_device_info()
        return {
            "status": "connected",
            "device": "Phicomm R1",
            "ip": adb.device_ip,
            "info": info
        }
    return {"status": "disconnected", "device": "Phicomm R1", "ip": None}


@router.post("/connect")
async def connect(ip: str, request: Request):
    """连接设备"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb:
        raise HTTPException(status_code=500, detail="ADB服务未初始化")

    success, msg = adb.connect(ip)
    if success:
        return {"success": True, "message": msg}
    else:
        raise HTTPException(status_code=400, detail=msg)


@router.post("/disconnect")
async def disconnect(request: Request):
    """断开连接"""
    adb = getattr(request.app.state, 'adb', None)
    if adb:
        adb.disconnect()
    return {"success": True}


@router.get("/screenshot")
async def take_screenshot(request: Request):
    """截屏 - 返回base64"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    # 临时文件路径
    import tempfile
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "screenshot.png")

    success, path = adb.screenshot(temp_path)
    if not success:
        raise HTTPException(status_code=500, detail=path)

    # 读取并转为base64
    try:
        with open(path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode()
        # 删除临时文件
        try:
            os.remove(path)
        except:
            pass
        return {"success": True, "image": img_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tap")
async def tap(x: int, y: int, request: Request):
    """点击屏幕"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    success, msg = adb.tap(x, y)
    if success:
        return {"success": True, "message": f"点击 ({x}, {y})"}
    raise HTTPException(status_code=500, detail=msg)


@router.post("/swipe")
async def swipe(direction: str, request: Request):
    """滑动屏幕"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    success, msg = adb.swipe(direction)
    if success:
        return {"success": True, "message": f"滑动 {direction}"}
    raise HTTPException(status_code=500, detail=msg)


@router.post("/volume")
async def volume(action: str, request: Request):
    """音量控制"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    if action == "up":
        success, msg = adb.volume_up()
    else:
        success, msg = adb.volume_down()

    if success:
        return {"success": True, "message": f"音量{action}"}
    raise HTTPException(status_code=500, detail=msg)


@router.get("/packages")
async def get_packages(request: Request, filter_type: str = "-3"):
    """获取应用列表"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        return {"packages": []}

    packages = adb.get_packages(filter_type)
    return {"packages": packages}


@router.post("/start")
async def start_app(
    package: str,
    activity: Optional[str] = None,
    service: Optional[str] = None,
    request: Request = None
):
    """启动应用"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    if activity:
        success, msg = adb.start_activity(package, activity)
    elif service:
        success, msg = adb.start_service(package, service)
    else:
        # 默认启动主Activity
        success, msg = adb.start_activity(package, ".MainActivity")

    if success:
        return {"success": True, "message": f"启动 {package}"}
    raise HTTPException(status_code=500, detail=msg)


@router.post("/stop")
async def stop_app(package: str, request: Request):
    """停止应用"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    success, msg = adb.force_stop(package)
    if success:
        return {"success": True, "message": f"停止 {package}"}
    raise HTTPException(status_code=500, detail=msg)


@router.get("/quick_actions")
async def quick_actions(request: Request):
    """快捷操作"""
    return {
        "actions": [
            {"name": "echo_service", "label": "启动EchoService", "package": "com.phicomm.speaker.player", "activity": ".EchoService"},
            {"name": "unisound", "label": "启动Unisound", "package": "com.phicomm.speaker.device", "activity": ".ui.MainActivity"},
            {"name": "settings", "label": "系统设置", "package": "com.android.settings", "activity": ".Settings"},
        ]
    }


@router.post("/audio/play")
async def play_audio(file_path: str, request: Request):
    """播放音频文件"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    success, msg = adb.play_audio(file_path)
    if success:
        return {"success": True, "message": f"播放 {file_path}"}
    raise HTTPException(status_code=500, detail=msg)


@router.post("/audio/stop")
async def stop_audio(request: Request):
    """停止播放"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    success, msg = adb.stop_audio()
    return {"success": True, "message": "已停止播放"}


@router.get("/audio/files")
async def get_audio_files(request: Request):
    """获取设备上的音频文件"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        return {"files": []}

    files = adb.get_audio_files()
    return {"files": files}


@router.post("/audio/record")
async def start_recorder(request: Request):
    """启动录音机"""
    adb = getattr(request.app.state, 'adb', None)
    if not adb or not adb.device_ip:
        raise HTTPException(status_code=400, detail="设备未连接")

    success, msg = adb.start_recorder()
    if success:
        return {"success": True, "message": "已启动录音机"}
    raise HTTPException(status_code=500, detail=msg)
