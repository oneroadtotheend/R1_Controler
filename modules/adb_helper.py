#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB Helper - 设备控制模块
"""

import subprocess
import time
import re


class ADBHelper:
    """ADB操作类"""

    def __init__(self):
        self.adb_path = "adb"
        self.device_ip = None

    def connect(self, ip):
        """连接设备"""
        self.device_ip = ip
        result = subprocess.run(
            [self.adb_path, "connect", ip],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "连接成功"
        return False, result.stderr

    def disconnect(self, ip=None):
        """断开连接"""
        ip = ip or self.device_ip
        if ip:
            subprocess.run([self.adb_path, "disconnect", ip], capture_output=True)

    def is_connected(self):
        """检查是否连接"""
        if not self.device_ip:
            return False
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "get-state"],
            capture_output=True,
            text=True
        )
        return "device" in result.stdout

    def shell(self, command: str, timeout: int = 30) -> str:
        """执行shell命令"""
        if not self.device_ip:
            return "Error: device not connected"
        cmd = [self.adb_path, "-s", self.device_ip, "shell", command]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout or result.stderr

    def screenshot(self, local_path):
        """截屏"""
        if not self.device_ip:
            return False, "未连接设备"

        # 设备截图
        subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "screencap", "-p", "/data/local/tmp/screen.png"],
            capture_output=True
        )
        # 拉取
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "pull", "/data/local/tmp/screen.png", local_path],
            capture_output=True
        )
        return result.returncode == 0, local_path

    def tap(self, x, y):
        """点击"""
        if not self.device_ip:
            return False, "未连接设备"
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "input", "tap", str(x), str(y)],
            capture_output=True
        )
        return result.returncode == 0, ""

    def swipe(self, direction):
        """滑动"""
        if not self.device_ip:
            return False, "未连接设备"

        # 方向参数
        swipe_map = {
            "left": (400, 260, 200, 260),
            "right": (200, 260, 400, 260),
            "up": (300, 400, 300, 200),
            "down": (300, 200, 300, 400)
        }
        coords = swipe_map.get(direction, (400, 260, 200, 260))

        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "input", "swipe"] + [str(c) for c in coords],
            capture_output=True
        )
        return result.returncode == 0, ""

    def keyevent(self, keycode):
        """按键"""
        if not self.device_ip:
            return False, "未连接设备"
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "input", "keyevent", str(keycode)],
            capture_output=True
        )
        return result.returncode == 0, ""

    def volume_up(self):
        """音量+"""
        return self.keyevent(24)

    def volume_down(self):
        """音量-"""
        return self.keyevent(25)

    def play_audio(self, file_path):
        """播放音频文件"""
        if not self.device_ip:
            return False, "未连接设备"

        # 先推送文件到设备
        device_path = "/sdcard/Music/temp_play.mp3"
        subprocess.run(
            [self.adb_path, "-s", self.device_ip, "push", file_path, device_path],
            capture_output=True
        )

        # 使用Intent播放
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "start",
             "-a", "android.intent.action.VIEW",
             "-d", f"file://{device_path}",
             "-t", "audio/mp3"],
            capture_output=True
        )
        return result.returncode == 0, ""

    def stop_audio(self):
        """停止播放"""
        if not self.device_ip:
            return False, "未连接设备"

        # 强制停止音乐播放器
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "force-stop",
             "com.android.music"],
            capture_output=True
        )
        # 也尝试停止其他音乐播放器
        subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "force-stop",
             "com.tencent.qqmusic"],
            capture_output=True
        )
        subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "force-stop",
             "com.netease.cloudmusic"],
            capture_output=True
        )
        return True, "已停止"

    def start_recorder(self):
        """启动系统录音机"""
        if not self.device_ip:
            return False, "未连接设备"

        # 尝试启动系统录音机
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am",
             "start", "-a", "android.provider.MediaStore.RECORD_SOUND"],
            capture_output=True
        )
        return result.returncode == 0, ""

    def get_audio_files(self):
        """获取设备上的音频文件"""
        if not self.device_ip:
            return []

        # 列出音乐目录
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell",
             "ls", "/sdcard/Music/"],
            capture_output=True,
            text=True
        )

        files = []
        for line in result.stdout.split('\n'):
            if line.strip() and ('.mp3' in line or '.wav' in line or '.m4a' in line):
                files.append(line.strip())

        return files

    def start_activity(self, package, activity):
        """启动Activity"""
        if not self.device_ip:
            return False, "未连接设备"
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "start", "-n", f"{package}/{activity}"],
            capture_output=True
        )
        return result.returncode == 0, ""

    def start_service(self, package, service):
        """启动Service"""
        if not self.device_ip:
            return False, "未连接设备"
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "startservice", f"{package}/{service}"],
            capture_output=True
        )
        return result.returncode == 0, ""

    def force_stop(self, package):
        """停止应用"""
        if not self.device_ip:
            return False, "未连接设备"
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "am", "force-stop", package],
            capture_output=True
        )
        return result.returncode == 0, ""

    def get_packages(self, filter_type="-3"):
        """获取应用列表"""
        if not self.device_ip:
            return []
        result = subprocess.run(
            [self.adb_path, "-s", self.device_ip, "shell", "pm", "list", "package", filter_type],
            capture_output=True,
            text=True
        )
        packages = []
        for line in result.stdout.split('\n'):
            if 'package:' in line:
                packages.append(line.replace('package:', '').strip())
        return packages

    def get_device_info(self):
        """获取设备信息"""
        if not self.device_ip:
            return {}

        info = {}
        commands = {
            "brand": "ro.product.brand",
            "model": "ro.product.model",
            "version": "ro.build.version.release",
            "sdk": "ro.build.version.sdk"
        }

        for key, prop in commands.items():
            result = subprocess.run(
                [self.adb_path, "-s", self.device_ip, "shell", "getprop", prop],
                capture_output=True,
                text=True
            )
            info[key] = result.stdout.strip()

        return info
