#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import device, llm, music, ha, config as config_api, voice
from modules.adb_helper import ADBHelper
from modules.llm_service import LLMService
from modules.music_service import MusicService
from modules.ha_service import HAService
from modules.service_monitor import R1ServiceMonitor
from modules.echo_service import EchoServiceController


# 项目根目录（基于本文件位置，确保PC与APK内都能正确定位）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_html(filename):
    """读取HTML文件"""
    path = os.path.join(ROOT_DIR, "app", "web", "templates", filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Template not found</h1>"


def create_app(config):
    """创建FastAPI应用"""

    app = FastAPI(
        title="斐讯R1智能控制中心",
        description="部署在斐讯R1设备上的Web控制面板",
        version="1.0.0"
    )

    # 静态文件目录
    static_dir = os.path.join(ROOT_DIR, "app", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 初始化服务
    adb = ADBHelper()
    llm_svc = LLMService(config)
    music_svc = MusicService(config)
    ha_svc = HAService(config)
    monitor = R1ServiceMonitor(config.get("device.ip"), adb)
    echo_svc = EchoServiceController(adb_helper=adb)

    # 存储到app state
    app.state.config = config
    app.state.adb = adb
    app.state.llm = llm_svc
    app.state.music = music_svc
    app.state.ha = ha_svc
    app.state.monitor = monitor
    app.state.echo = echo_svc

    # 注册监控路由
    from modules.service_monitor import create_monitor_routes
    create_monitor_routes(app, monitor)

    # 注册路由
    app.include_router(device.router, prefix="/api/device", tags=["设备控制"])
    app.include_router(llm.router, prefix="/api/llm", tags=["大模型"])
    app.include_router(music.router, prefix="/api/music", tags=["音乐服务"])
    app.include_router(ha.router, prefix="/api/ha", tags=["智能家居"])
    app.include_router(config_api.router, prefix="/api/config", tags=["配置"])
    app.include_router(voice.router, prefix="/api/voice", tags=["语音控制"])

    # Web页面路由 - 直接返回HTML
    @app.get("/", response_class=HTMLResponse)
    async def home():
        """主页"""
        return read_html("index.html")

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page():
        """设置页面"""
        return read_html("settings.html")

    @app.get("/music", response_class=HTMLResponse)
    async def music_page():
        """音乐页面"""
        return read_html("music.html")

    @app.get("/ha", response_class=HTMLResponse)
    async def ha_page():
        """智能家居页面"""
        return read_html("ha.html")

    @app.get("/chat", response_class=HTMLResponse)
    async def chat_page():
        """对话页面"""
        return read_html("chat.html")

    @app.get("/voice", response_class=HTMLResponse)
    async def voice_page():
        """语音控制页面"""
        return read_html("voice.html")

    @app.get("/monitor", response_class=HTMLResponse)
    async def monitor_page():
        """服务监控页面"""
        return read_html("monitor.html")

    return app
