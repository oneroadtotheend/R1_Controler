#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
"""

import json
import os
from pathlib import Path


class ConfigManager:
    """配置管理器"""

    @staticmethod
    def _resolve_config_dir():
        """解析配置目录：APK 运行时源码目录可能只读，改写到可写的应用私有目录。"""
        android_arg = os.environ.get('ANDROID_ARGUMENT')
        if android_arg:
            # ANDROID_ARGUMENT 为 APK 内 main.py 的绝对路径，其所在目录可写
            base = os.path.dirname(android_arg)  # .../files/app
            cfg = os.path.join(base, ".r1config")
            try:
                os.makedirs(cfg, exist_ok=True)
            except Exception:
                pass
            return Path(cfg)
        # PC / 开发模式：就用源码内的 config 目录
        return Path(__file__).parent

    def __init__(self):
        self.config_dir = self._resolve_config_dir()
        self.config_file = self.config_dir / "settings.json"

        # 默认配置
        self.config = {
            # 服务器配置
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "debug": True
            },
            # 大模型配置
            "llm": {
                "enabled": False,
                "api_url": "https://api.openai.com/v1",
                "api_key": "",
                "model": "gpt-3.5-turbo",
                "system_prompt": "你是一个智能家居助手，可以帮助用户控制斐讯R1智能音箱和Home Assistant智能家居设备。请用中文回复。",
                "temperature": 0.7
            },
            # 音乐服务配置
            "music": {
                "enabled": False,
                "source": "netEase",
                "local_api_url": "http://localhost:3000",  # 本地API地址
                "cookie": "",
                "qrcode_login": True,
                "sync_favorites": True
            },
            # Home Assistant配置
            "home_assistant": {
                "enabled": False,
                "url": "http://192.168.1.x:8123",
                "token": "",
                "auto_refresh": True
            }
        }

    def load(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._merge(self.config, loaded)
            except Exception as e:
                print(f"加载配置失败: {e}")
        else:
            self.save()

    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def _merge(self, default, loaded):
        """递归合并"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge(default[key], value)
                else:
                    default[key] = value

    def get(self, key, default=None):
        """获取配置"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        """设置配置"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_all(self):
        """获取全部配置"""
        return self.config
