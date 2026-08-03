#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐服务API
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import qrcode
import io
import base64

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    """获取音乐服务状态"""
    config = getattr(request.app.state, 'config', None)
    music = getattr(request.app.state, 'music', None)

    if not config or not music:
        return {"logged_in": False, "source": "netEase"}

    logged_in = bool(config.get("music.cookie", ""))
    return {
        "logged_in": logged_in,
        "source": config.get("music.source", "netEase")
    }


@router.get("/qrcode")
async def get_qrcode(request: Request):
    """获取二维码"""
    music = getattr(request.app.state, 'music', None)

    if not music:
        raise HTTPException(status_code=500, detail="服务未初始化")

    try:
        qr_data = music.get_qrcode()

        # 生成二维码图片
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(qr_data.get('qrurl', ''))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 转为base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "unikey": qr_data.get('unikey', ''),
            "qrcode": img_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qrcode/status")
async def check_qrcode_status(unikey: str, request: Request):
    """检查二维码状态"""
    music = getattr(request.app.state, 'music', None)

    if not music:
        raise HTTPException(status_code=500, detail="服务未初始化")

    try:
        status = music.check_qrcode_status(unikey)

        if status == 'SUCCESS':
            # 保存登录状态
            config = getattr(request.app.state, 'config', None)
            if config:
                # 获取cookie
                config.set("music.logged_in", True)
                config.save()

            return {"status": "SUCCESS", "message": "登录成功"}

        return {"status": status, "message": "等待确认"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


@router.post("/cookie")
async def login_with_cookie(cookie: str, request: Request):
    """Cookie登录"""
    config = getattr(request.app.state, 'config', None)
    music = getattr(request.app.state, 'music', None)

    if not config or not music:
        raise HTTPException(status_code=500, detail="服务未初始化")

    if music.login_with_cookie(cookie):
        config.set("music.cookie", cookie)
        config.save()
        return {"success": True, "message": "登录成功"}
    else:
        return {"success": False, "message": "Cookie无效"}


@router.post("/logout")
async def logout(request: Request):
    """退出登录"""
    config = getattr(request.app.state, 'config', None)
    if config:
        config.set("music.cookie", "")
        config.save()
    return {"success": True}


@router.post("/search")
async def search(request: Request):
    """搜索音乐"""
    config = getattr(request.app.state, 'config', None)
    music = getattr(request.app.state, 'music', None)

    if not config or not music:
        raise HTTPException(status_code=500, detail="服务未初始化")

    data = await request.json()
    keyword = data.get("keyword", "")
    source = data.get("source", config.get("music.source", "netEase"))

    if not keyword:
        raise HTTPException(status_code=400, detail="请输入搜索关键词")

    try:
        results = music.search(keyword, source)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.post("/play")
async def play(request: Request):
    """播放 - 在R1上播放音乐"""
    config = getattr(request.app.state, 'config', None)
    music = getattr(request.app.state, 'music', None)
    echo = getattr(request.app.state, 'echo', None)

    if not config or not music:
        raise HTTPException(status_code=500, detail="服务未初始化")

    data = await request.json()
    song_id = data.get("song_id")
    song_name = data.get("name", "")
    artist = data.get("artist", "")
    source = data.get("source", config.get("music.source", "netEase"))

    if not song_id:
        raise HTTPException(status_code=400, detail="请选择歌曲")

    # 获取播放地址
    try:
        play_url_data = music.get_play_url(song_id)
        if not play_url_data or not play_url_data.get('url'):
            return {"success": False, "message": "无法获取播放地址"}

        play_url = play_url_data.get('url')

        # 如果有EchoService，让R1播放
        if echo:
            try:
                echo.play_url(play_url, song_name, artist)
                return {
                    "success": True,
                    "url": play_url,
                    "message": "已在R1上开始播放"
                }
            except Exception as e:
                return {
                    "success": True,
                    "url": play_url,
                    "message": f"获取播放地址成功，但R1播放失败: {str(e)}"
                }

        return {
            "success": True,
            "url": play_url,
            "message": "获取播放地址成功"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/pause")
async def pause(request: Request):
    """暂停"""
    echo = getattr(request.app.state, 'echo', None)
    if echo:
        try:
            echo.play_pause()
        except:
            pass
    return {"success": True, "message": "暂停播放"}


@router.post("/next")
async def next_song(request: Request):
    """下一首"""
    echo = getattr(request.app.state, 'echo', None)
    if echo:
        try:
            echo.next()
        except:
            pass
    return {"success": True, "message": "下一首"}


@router.post("/prev")
async def prev_song(request: Request):
    """上一首"""
    echo = getattr(request.app.state, 'echo', None)
    if echo:
        try:
            echo.prev()
        except:
            pass
    return {"success": True, "message": "上一首"}
