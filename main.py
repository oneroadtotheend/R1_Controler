#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斐讯R1智能控制中心 - Web版
部署在斐讯R1设备上，通过浏览器访问管理

两种运行模式：
  - PC模式：直接 uvicorn 运行，浏览器访问
  - Android模式(打包为APK)：Kivy WebView 内嵌浏览器加载本地FastAPI服务
"""

import os
import uvicorn
from app import create_app
from config.config_manager import ConfigManager


def _build_app():
    config = ConfigManager()
    config.load()
    app = create_app(config)
    return config, app


def run_pc():
    """PC模式：直接运行Web服务"""
    config, app = _build_app()
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 8080)
    print(f"🚀 斐讯R1智能控制中心 启动中...")
    print(f"📱 请在浏览器访问: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    # R1资源有限，不启用reload
    uvicorn.run(app, host=host, port=port, reload=False)


def run_android():
    """Android模式(APK)：Kivy承载WebView加载本地FastAPI"""
    import threading
    import time

    config, app = _build_app()
    port = config.get("server.port", 8080)

    def start_server():
        # 监听所有网卡，便于从其他设备浏览器访问；本机WebView用127.0.0.1回环
        uvicorn.run(app, host="0.0.0.0", port=port, reload=False)

    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    time.sleep(3)

    from kivy.app import App
    from kivy.uix.webview import WebView

    class R1App(App):
        def build(self):
            wv = WebView(url=f"http://127.0.0.1:{port}")
            wv.size_hint = (1, 1)
            return wv

    R1App().run()


if __name__ == "__main__":
    # python-for-android 在APK运行时会设置 ANDROID_ARGUMENT 环境变量
    if os.environ.get('ANDROID_ARGUMENT'):
        run_android()
    else:
        run_pc()
