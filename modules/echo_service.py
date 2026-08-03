#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斐讯R1 EchoService 集成模块

功能：
- 启动/停止 EchoService
- 语音控制（播放/暂停/上一首/下一首）
- 播放音乐/有声书
- 控制音量
"""

import subprocess
import json
import time
import requests
from typing import Optional, Dict, Any, Callable
from enum import Enum


class PlayMode(Enum):
    """播放模式"""
    顺序 = 1
    随机 = 2
    单曲循环 = 3


class EchoServiceController:
    """EchoService 控制器"""
    
    # EchoService 包信息
    PACKAGE_NAME = "com.phicomm.speaker.player"
    SERVICE_NAME = "com.phicomm.speaker.player.service.EchoService"
    ACTIVITY_NAME = "com.phicomm.speaker.player.ui.MainActivity"
    
    # 广播Actions
    ACTION_PLAY = "com.phicomm.speaker.player.ACTION_PLAY"
    ACTION_PAUSE = "com.phicomm.speaker.player.ACTION_PAUSE"
    ACTION_NEXT = "com.phicomm.speaker.player.ACTION_NEXT"
    ACTION_PREV = "com.phicomm.speaker.player.ACTION_PREV"
    ACTION_STOP = "com.phicomm.speaker.player.ACTION_STOP"
    
    def __init__(self, device_ip: str = None, adb_helper=None):
        """
        初始化
        
        Args:
            device_ip: 斐讯R1的IP地址
            adb_helper: ADBHelper实例
        """
        self.device_ip = device_ip
        self.adb = adb_helper
    
    def _run_shell(self, command: str) -> str:
        """执行ADB shell命令"""
        if self.adb:
            return self.adb.shell(command)
        # 直接执行（用于测试）
        cmd = f"adb shell {command}" if self.device_ip else command
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    
    # ========== 服务控制 ==========
    
    def start_service(self) -> bool:
        """启动EchoService"""
        cmd = f"am startservice -n {self.SERVICE_NAME}"
        result = self._run_shell(cmd)
        return "Starting service" in result or "started" in result.lower()
    
    def stop_service(self) -> bool:
        """停止EchoService"""
        cmd = f"am stopservice -n {self.SERVICE_NAME}"
        result = self._run_shell(cmd)
        return True
    
    def start_app(self) -> bool:
        """启动EchoService应用"""
        cmd = f"am start -n {self.PACKAGE_NAME}/{self.ACTIVITY_NAME}"
        result = self._run_shell(cmd)
        return "Starting" in result
    
    def is_service_running(self) -> bool:
        """检查服务是否运行"""
        cmd = f"dumpsys activity services | grep {self.PACKAGE_NAME}"
        result = self._run_shell(cmd)
        return self.PACKAGE_NAME in result
    
    # ========== 播放控制 ==========
    
    def play(self) -> bool:
        """播放"""
        cmd = f"am broadcast -a {self.ACTION_PLAY}"
        self._run_shell(cmd)
        return True
    
    def pause(self) -> bool:
        """暂停"""
        cmd = f"am broadcast -a {self.ACTION_PAUSE}"
        self._run_shell(cmd)
        return True
    
    def play_pause(self) -> bool:
        """播放/暂停切换"""
        cmd = f"am broadcast -a android.intent.action.MEDIA_BUTTON --ei keycode 85"
        self._run_shell(cmd)
        return True
    
    def next(self) -> bool:
        """下一首"""
        cmd = f"am broadcast -a {self.ACTION_NEXT}"
        self._run_shell(cmd)
        return True
    
    def prev(self) -> bool:
        """上一首"""
        cmd = f"am broadcast -a {self.ACTION_PREV}"
        self._run_shell(cmd)
        return True
    
    def stop(self) -> bool:
        """停止"""
        cmd = f"am broadcast -a {self.ACTION_STOP}"
        self._run_shell(cmd)
        return True
    
    def seek_to(self, position: int) -> bool:
        """跳转到指定位置（毫秒）"""
        cmd = f"am broadcast -a com.phicomm.speaker.player.ACTION_SEEK --ei position {position}"
        self._run_shell(cmd)
        return True
    
    # ========== 播放列表控制 ==========
    
    def play_url(self, url: str, title: str = "", artist: str = "") -> bool:
        """播放网络URL

        Args:
            url: 音频URL
            title: 歌曲标题
            artist: 艺术家
        """
        # 方法1: 使用广播通知EchoService播放（推荐）
        cmd1 = (
            f"am broadcast -a com.phicomm.speaker.player.ACTION_PLAY_URL "
            f"--es url '{url}' "
            f"--es title '{title}' "
            f"--es artist '{artist}'"
        )
        self._run_shell(cmd1)

        # 方法2: 如果广播不行，尝试用Intent启动EchoService
        cmd2 = (
            f"am start -n com.phicomm.speaker.player/"
            f"-a android.intent.action.VIEW "
            f"-d '{url}' "
            f"-t 'audio/*'"
        )
        self._run_shell(cmd2)
        return True
    
    def play_music_by_keyword(self, keyword: str) -> bool:
        """通过关键词搜索并播放音乐
        
        这会启动EchoService的音乐搜索功能
        """
        # 通过广播发送搜索请求
        cmd = (
            f"am broadcast -a com.phicomm.speaker.player.ACTION_SEARCH_MUSIC "
            f"--es keyword '{keyword}'"
        )
        self._run_shell(cmd)
        return True
    
    # ========== 音量控制 ==========
    
    def volume_up(self) -> bool:
        """音量+"""
        cmd = "input keyevent 24"  # KEYCODE_VOLUME_UP
        self._run_shell(cmd)
        return True
    
    def volume_down(self) -> bool:
        """音量-"""
        cmd = "input keyevent 25"  # KEYCODE_VOLUME_DOWN
        self._run_shell(cmd)
        return True
    
    def set_volume(self, level: int) -> bool:
        """设置音量 (0-15)"""
        # 先获取当前音量，再调整
        cmd = f"media volume --show --stream 3 --set {level}"
        self._run_shell(cmd)
        return True
    
    # ========== 状态获取 ==========
    
    def get_player_status(self) -> Dict[str, Any]:
        """获取播放器状态"""
        # 通过 dumpsys 获取媒体播放信息
        cmd = "dumpsys media_session | grep -A 50 'PlaybackState'"
        result = self._run_shell(cmd)
        
        status = {
            "is_playing": "state=3" in result or "Playing" in result,
            "position": 0,
            "duration": 0,
            "title": "",
            "artist": ""
        }
        
        # 解析状态
        for line in result.split('\n'):
            if "position" in line.lower():
                try:
                    status["position"] = int(line.split(':')[-1].strip())
                except:
                    pass
            if "duration" in line.lower():
                try:
                    status["duration"] = int(line.split(':')[-1].strip())
                except:
                    pass
        
        return status
    
    def get_current_song(self) -> Dict[str, str]:
        """获取当前播放的歌曲信息"""
        cmd = "dumpsys media_session | grep -A 5 'Metadata'"
        result = self._run_shell(cmd)
        
        song = {
            "title": "",
            "artist": "",
            "album": ""
        }
        
        # 解析元数据
        lines = result.split('\n')
        for i, line in enumerate(lines):
            if "title" in line.lower():
                song["title"] = lines[i+1].strip() if i+1 < len(lines) else ""
            if "artist" in line.lower():
                song["artist"] = lines[i+1].strip() if i+1 < len(lines) else ""
        
        return song
    
    # ========== TTS 语音播报 ==========
    
    def speak(self, text: str) -> bool:
        """语音播报文字
        
        使用EchoService的TTS功能播报
        """
        # 发送广播通知TTS播报
        cmd = (
            f"am broadcast -a com.phicomm.speaker.player.ACTION_TTS "
            f"--es text '{text}'"
        )
        self._run_shell(cmd)
        return True
    
    def announce(self, message: str) -> bool:
        """播报通知"""
        return self.speak(message)


class VoiceAssistant:
    """语音助手 - 整合LLM和EchoService"""
    
    def __init__(self, 
                 echo_controller: EchoServiceController,
                 llm_service=None,
                 ha_service=None,
                 music_service=None):
        """
        初始化语音助手
        
        Args:
            echo_controller: EchoService控制器
            llm_service: 大模型服务
            ha_service: HomeAssistant服务
            music_service: 音乐服务
        """
        self.echo = echo_controller
        self.llm = llm_service
        self.ha = ha_service
        self.music = music_service
        
        # 意图识别关键词映射
        self.intent_keywords = {
            "播放音乐": ["播放音乐", "放首歌", "唱首歌", "听歌", "播放歌曲"],
            "暂停": ["暂停", "停止播放", "别放了"],
            "继续": ["继续", "继续播放", "接着放"],
            "下一首": ["下一首", "切歌", "下一曲"],
            "上一首": ["上一首", "上一曲", "往前"],
            "音量加": ["声音大点", "大声点", "音量加"],
            "音量减": ["声音小点", "小声点", "音量减"],
            "开灯": ["开灯", "打开灯", "灯打开"],
            "关灯": ["关灯", "关灯", "灯关闭"],
            "查询天气": ["天气", "今天天气", "怎么样"],
        }
    
    def recognize_intent(self, text: str) -> str:
        """
        识别用户意图
        
        Args:
            text: 用户说的文本
            
        Returns:
            意图类型
        """
        # 先尝试LLM识别
        if self.llm:
            prompt = f"""请识别用户意图，只返回意图类型，不要其他内容。

用户说: {text}

可能的意图:
- 播放音乐
- 暂停
- 继续
- 下一首
- 上一首
- 音量加
- 音量减
- 开灯
- 关灯
- 查询天气
- 闲聊
- 其他

返回:"""
            try:
                result = self.llm.chat(prompt)
                # 解析结果
                for intent in self.intent_keywords.keys():
                    if intent in result:
                        return intent
                if "播放" in result or "音乐" in result:
                    return "播放音乐"
                if "天气" in result:
                    return "查询天气"
            except:
                pass
        
        # fallback到关键词匹配
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return intent
        
        return "闲聊"
    
    def execute_intent(self, intent: str, text: str = "") -> str:
        """
        执行意图
        
        Args:
            intent: 意图类型
            text: 用户原始文本
            
        Returns:
            回复文本
        """
        # 提取关键词（用于搜索等）
        import re
        # 移除常见词，保留搜索关键词
        search_text = text.replace("播放", "").replace("听", "").replace("我要", "").replace("帮我", "").strip()
        
        if intent == "播放音乐":
            if search_text:
                # 搜索并播放
                self.echo.play_music_by_keyword(search_text)
                return f"好的，播放{search_text}"
            else:
                # 播放默认列表
                self.echo.play()
                return "好的，开始播放音乐"
        
        elif intent == "暂停":
            self.echo.pause()
            return "已暂停"
        
        elif intent == "继续":
            self.echo.play()
            return "继续播放"
        
        elif intent == "下一首":
            self.echo.next()
            return "切换到下一首"
        
        elif intent == "上一首":
            self.echo.prev()
            return "切换到上一首"
        
        elif intent == "音量加":
            self.echo.volume_up()
            return "音量已增加"
        
        elif intent == "音量减":
            self.echo.volume_down()
            return "音量已减小"
        
        elif intent == "开灯":
            if self.ha:
                # 控制HomeAssistant设备
                self.ha.turn_on("light")
                return "已打开灯光"
            return "已打开灯光（模拟）"
        
        elif intent == "关灯":
            if self.ha:
                self.ha.turn_off("light")
                return "已关闭灯光"
            return "已关闭灯光（模拟）"
        
        elif intent == "查询天气":
            # 可以调用天气API
            return "今天天气晴朗，温度25度"
        
        elif intent == "闲聊":
            if self.llm:
                result = self.llm.chat(text)
                self.echo.speak(result)
                return result
            return "抱歉，我还没有接入大模型"
        
        return "好的"
    
    def handle_voice_command(self, text: str) -> str:
        """
        处理语音命令的完整流程
        
        Args:
            text: 用户语音转文字的结果
            
        Returns:
            回复文本
        """
        # 1. 识别意图
        intent = self.recognize_intent(text)
        
        # 2. 执行意图
        response = self.execute_intent(intent, text)
        
        # 3. 语音播报
        self.echo.speak(response)
        
        return response
    
    def start_voice_wakeup(self):
        """启动语音唤醒
        
        通过启动EchoService来实现语音唤醒
        """
        # 启动EchoService
        self.echo.start_service()
        return "语音唤醒已启动，请说唤醒词"


# ========== 独立运行测试 ==========

if __name__ == "__main__":
    # 测试代码
    echo = EchoServiceController("192.168.1.100")
    
    # 测试播放
    # echo.play_url("https://music.163.com/song/media/outer/url?id=123456.mp3", "测试歌曲", "测试歌手")
    
    # 测试语音播报
    echo.speak("你好，我是斐讯R1智能音响")
    
    print("测试完成")
