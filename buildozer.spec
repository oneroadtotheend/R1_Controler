[app]

# 应用名称与包名
title = R1智能控制中心
package.name = controller
package.domain = com.r1controller

# 源码目录（项目根）
source.dir = .
source.include_exts = py,png,jpg,kv,json,html,js,css,ttf,db,zip,txt
source.include_patterns = app/*,modules/*,config/*

# 版本号（对应 R1_controler_2.0.0）
version = 2.0.0

# 依赖（锁定纯Python版本，避免 pydantic v2 的 Rust 扩展在 p4a 无法编译）
requirements = python3==3.11.9,kivy==2.2.1,pyjnius,fastapi==0.95.2,uvicorn==0.23.2,jinja2==3.1.2,pyyaml==6.0.1,requests==2.31.0,qrcode==7.4.2,pillow==10.1.0,pydantic==1.10.13

# 横竖屏都支持
orientation = portrait
fullscreen = True

# 入口
android.entrypoint = main.py

# 权限：联网加载Web资源/外部CDN、录音(语音)、唤醒锁(防休眠)
android.permissions = INTERNET,ACCESS_NETWORK_STATE,RECORD_AUDIO,WAKE_LOCK,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android API 级别（R1 为老设备，min 21 兼容）
android.targetapi = 31
android.minapi = 21
android.accept_sdk_license = True
android.wakelock = True

# 架构：R1 (RK3229) 为 ARMv7 32位
android.archs = armeabi-v7a

# 允许明文(http)流量：WebView 需要加载本地 http://127.0.0.1 的 FastAPI 服务
android.allow_cleartext_traffic = True
android.private_storage = True

# p4a 用 master 分支(stable 没有 --only-binary=:all: 限制,会直接装失败)
p4a.branch = master

log_level = 2
build_type = debug

[buildozer]
log_level = 2
warn_on_root = 0
build_dir = ./build
bin_dir = ./bin
