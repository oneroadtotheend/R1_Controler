#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斐讯R1智能控制中心 - 语音对话API

提供语音命令处理接口
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(tags=["语音控制"])

# 全局语音处理器
_voice_processor = None


def init_voice_processor(config: Dict[str, Any]):
    """初始化语音处理器"""
    global _voice_processor
    from modules.voice_processor import VoiceCommandProcessor
    _voice_processor = VoiceCommandProcessor(config)


class VoiceCommandRequest(BaseModel):
    """语音命令请求"""
    text: str
    use_llm: bool = True


class VoiceCommandResponse(BaseModel):
    """语音命令响应"""
    success: bool
    intent: str
    response: str
    details: Optional[Dict[str, Any]] = None


@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(req: VoiceCommandRequest, request: Request):
    """
    处理语音命令
    
    用户发送文本命令，系统识别意图并执行
    """
    global _voice_processor
    
    if not _voice_processor:
        # 尝试获取配置
        config = getattr(request.app.state, 'config', None)
        if config:
            init_voice_processor({
                "device_ip": config.get("device.ip", "")
            })
        else:
            return VoiceCommandResponse(
                success=False,
                intent="error",
                response="语音处理器未初始化"
            )
    
    try:
        # 处理命令
        response = _voice_processor.process(req.text)
        
        return VoiceCommandResponse(
            success=True,
            intent="unknown",
            response=response
        )
    except Exception as e:
        return VoiceCommandResponse(
            success=False,
            intent="error",
            response=f"处理失败: {str(e)}"
        )


@router.get("/status")
async def get_voice_status(request: Request):
    """获取语音服务状态"""
    global _voice_processor
    
    return {
        "enabled": _voice_processor is not None,
        "llm_enabled": True,
        "echo_service_available": True
    }


@router.post("/wakeup")
async def start_wakeup(request: Request):
    """启动语音唤醒"""
    global _voice_processor
    
    if not _voice_processor:
        return {"success": False, "message": "语音处理器未初始化"}
    
    try:
        result = _voice_processor.echo.start_voice_wakeup()
        return {"success": True, "message": result}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ========== 集成EchoService控制 ==========

from modules.echo_service import EchoServiceController

@router.post("/echo/play")
async def echo_play(request: Request):
    """EchoService播放"""
    config = getattr(request.app.state, 'config', None)
    device_ip = config.get("device.ip", "") if config else ""
    
    echo = EchoServiceController(device_ip)
    echo.play()
    
    return {"success": True, "message": "已播放"}


@router.post("/echo/pause")
async def echo_pause(request: Request):
    """EchoService暂停"""
    config = getattr(request.app.state, 'config', None)
    device_ip = config.get("device.ip", "") if config else ""
    
    echo = EchoServiceController(device_ip)
    echo.pause()
    
    return {"success": True, "message": "已暂停"}


@router.post("/echo/next")
async def echo_next(request: Request):
    """EchoService下一首"""
    config = getattr(request.app.state, 'config', None)
    device_ip = config.get("device.ip", "") if config else ""
    
    echo = EchoServiceController(device_ip)
    echo.next()
    
    return {"success": True, "message": "已切换到下一首"}


@router.post("/echo/volume/up")
async def echo_volume_up(request: Request):
    """音量增加"""
    config = getattr(request.app.state, 'config', None)
    device_ip = config.get("device.ip", "") if config else ""
    
    echo = EchoServiceController(device_ip)
    echo.volume_up()
    
    return {"success": True, "message": "音量已增加"}


@router.post("/echo/volume/down")
async def echo_volume_down(request: Request):
    """音量减少"""
    config = getattr(request.app.state, 'config', None)
    device_ip = config.get("device.ip", "") if config else ""
    
    echo = EchoServiceController(device_ip)
    echo.volume_down()
    
    return {"success": True, "message": "音量已减小"}


@router.post("/echo/speak")
async def echo_speak(text: str, request: Request):
    """语音播报"""
    config = getattr(request.app.state, 'config', None)
    device_ip = config.get("device.ip", "") if config else ""
    
    echo = EchoServiceController(device_ip)
    echo.speak(text)
    
    return {"success": True, "message": f"正在播报: {text}"}
