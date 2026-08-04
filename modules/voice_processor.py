#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音指令处理模块

功能：
- 意图识别
- 动作执行
- LLM对话整合
"""

from typing import Dict, Any, Optional, Callable
import re


class Intent:
    """意图定义"""
    PLAY_MUSIC = "播放音乐"
    PAUSE = "暂停"
    RESUME = "继续"
    NEXT = "下一首"
    PREV = "上一首"
    VOLUME_UP = "音量加"
    VOLUME_DOWN = "音量减"
    TTS_SPEAK = "语音播报"
    CONTROL_LIGHT_ON = "开灯"
    CONTROL_LIGHT_OFF = "关灯"
    CONTROL_DEVICE = "控制设备"
    QUERY_WEATHER = "查询天气"
    QUERY_TIME = "查询时间"
    CHAT = "闲聊"
    UNKNOWN = "未知"


class IntentRecognizer:
    """意图识别器"""
    
    # 意图关键词映射
    KEYWORDS = {
        Intent.PLAY_MUSIC: [
            "播放", "放首歌", "唱首歌", "听歌", "播放音乐", "来首歌",
            "放一首", "播放歌曲", "我想听", "点歌"
        ],
        Intent.PAUSE: [
            "暂停", "停止播放", "别放了", "先别放", "停一下"
        ],
        Intent.RESUME: [
            "继续", "继续播放", "接着放", "继续放", "恢复播放"
        ],
        Intent.NEXT: [
            "下一首", "切歌", "下一曲", "换一首", "换一个"
        ],
        Intent.PREV: [
            "上一首", "上一曲", "往回", "上一个"
        ],
        Intent.VOLUME_UP: [
            "声音大点", "大声点", "调大点", "音量加", "大点声"
        ],
        Intent.VOLUME_DOWN: [
            "声音小点", "小声点", "调小点", "音量减", "小点声"
        ],
        Intent.CONTROL_LIGHT_ON: [
            "开灯", "打开灯", "灯打开", "把灯打开", "开一下灯"
        ],
        Intent.CONTROL_LIGHT_OFF: [
            "关灯", "关闭灯", "灯关闭", "把灯关掉", "关一下灯"
        ],
        Intent.QUERY_WEATHER: [
            "天气", "今天天气", "明天天气", "怎么样", "多少度"
        ],
        Intent.QUERY_TIME: [
            "几点", "时间", "现在几点", "几点了", "什么时间"
        ],
    }
    
    # 设备控制关键词
    DEVICE_PATTERNS = [
        (r"(开|关|打开|关闭)(.*)灯", "灯"),
        (r"(开|关|打开|关闭)(.*)空调", "空调"),
        (r"(开|关|打开|关闭)(.*)风扇", "风扇"),
        (r"(开|关|打开|关闭)(.*)电视", "电视"),
        (r"(开|关|打开|关闭)(.*)空调", "空调"),
        (r"调(高|低|升|降)(.*)温度", "温度"),
        (r"设置(.*)度", "温度"),
    ]
    
    def __init__(self, llm_service=None):
        """
        初始化
        
        Args:
            llm_service: 大模型服务（可选，用于高级意图识别）
        """
        self.llm = llm_service
    
    def recognize(self, text: str) -> tuple[str, Dict[str, Any]]:
        """
        识别意图
        
        Args:
            text: 用户文本
            
        Returns:
            (意图类型, 提取的参数)
        """
        text = text.strip()
        params = {"raw_text": text, "keywords": ""}
        
        # 1. 关键词匹配
        for intent, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    # 提取搜索关键词
                    if intent == Intent.PLAY_MUSIC:
                        # 提取歌曲名
                        params["keywords"] = text
                        for kw in ["播放", "听", "我想", "我要", "帮我"]:
                            params["keywords"] = params["keywords"].replace(kw, "")
                        params["keywords"] = params["keywords"].strip()
                    
                    return intent, params
        
        # 2. 正则匹配设备控制
        for pattern, device_type in self.DEVICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                action = match.group(1)
                device = match.group(2).strip() if match.group(2) else device_type
                params["device"] = device
                params["action"] = "开" if action in ["开", "打开"] else "关"
                
                if action in ["开", "打开"]:
                    return Intent.CONTROL_DEVICE, params
                elif action in ["关", "关闭"]:
                    return Intent.CONTROL_DEVICE, params
        
        # 3. LLM识别（如果有）
        if self.llm:
            try:
                intent, params = self._llm_recognize(text)
                if intent != Intent.UNKNOWN:
                    return intent, params
            except:
                pass
        
        # 4. 默认闲聊
        return Intent.CHAT, params
    
    def _llm_recognize(self, text: str) -> tuple[str, Dict[str, Any]]:
        """使用LLM识别意图"""
        prompt = f"""你是一个意图识别助手。请识别用户指令的意图。

用户说: {text}

可选意图:
- 播放音乐
- 暂停
- 继续
- 下一首
- 上一首
- 音量加
- 音量减
- 开灯
- 关灯
- 控制空调
- 查询天气
- 查询时间
- 闲聊

请以JSON格式返回:
{{"intent": "意图名称", "keywords": "提取的关键词", "entity": "实体名称"}}

只返回JSON，不要其他内容。"""
        
        result = self.llm.chat(prompt)
        
        # 解析JSON
        try:
            import json
            data = json.loads(result)
            intent = data.get("intent", Intent.UNKNOWN)
            params = {
                "raw_text": text,
                "keywords": data.get("keywords", ""),
                "entity": data.get("entity", "")
            }
            return intent, params
        except:
            return Intent.UNKNOWN, {}


class ActionExecutor:
    """动作执行器"""
    
    def __init__(self,
                 echo_controller=None,
                 ha_service=None,
                 music_service=None,
                 llm_service=None):
        """
        初始化
        
        Args:
            echo_controller: EchoService控制器
            ha_service: HomeAssistant服务
            music_service: 音乐服务
            llm_service: 大模型服务
        """
        self.echo = echo_controller
        self.ha = ha_service
        self.music = music_service
        self.llm = llm_service
        
        # 动作处理函数映射
        self.action_handlers = {
            Intent.PLAY_MUSIC: self._handle_play_music,
            Intent.PAUSE: self._handle_pause,
            Intent.RESUME: self._handle_resume,
            Intent.NEXT: self._handle_next,
            Intent.PREV: self._handle_prev,
            Intent.VOLUME_UP: self._handle_volume_up,
            Intent.VOLUME_DOWN: self._handle_volume_down,
            Intent.CONTROL_DEVICE: self._handle_control_device,
            Intent.QUERY_WEATHER: self._handle_weather,
            Intent.QUERY_TIME: self._handle_time,
            Intent.CHAT: self._handle_chat,
        }
    
    def execute(self, intent: str, params: Dict[str, Any]) -> str:
        """
        执行动作
        
        Args:
            intent: 意图类型
            params: 意图参数
            
        Returns:
            回复文本
        """
        handler = self.action_handlers.get(intent)
        if handler:
            return handler(params)
        return "好的"
    
    def _handle_play_music(self, params: Dict[str, Any]) -> str:
        """播放音乐"""
        keywords = params.get("keywords", "")
        
        if keywords:
            # 搜索播放
            if self.music:
                # 通过音乐服务搜索
                self.echo.play_music_by_keyword(keywords)
                return f"好的，播放{keywords}"
            else:
                self.echo.play_music_by_keyword(keywords)
                return f"好的，播放{keywords}"
        else:
            # 播放默认
            self.echo.play()
            return "好的，播放音乐"
    
    def _handle_pause(self, params: Dict[str, Any]) -> str:
        """暂停"""
        self.echo.pause()
        return "已暂停"
    
    def _handle_resume(self, params: Dict[str, Any]) -> str:
        """继续播放"""
        self.echo.play()
        return "继续播放"
    
    def _handle_next(self, params: Dict[str, Any]) -> str:
        """下一首"""
        self.echo.next()
        return "切换到下一首"
    
    def _handle_prev(self, params: Dict[str, Any]) -> str:
        """上一首"""
        self.echo.prev()
        return "切换到上一首"
    
    def _handle_volume_up(self, params: Dict[str, Any]) -> str:
        """音量增加"""
        self.echo.volume_up()
        return "音量已增加"
    
    def _handle_volume_down(self, params: Dict[str, Any]) -> str:
        """音量减少"""
        self.echo.volume_down()
        return "音量已减小"
    
    def _handle_control_device(self, params: Dict[str, Any]) -> str:
        """控制设备"""
        device = params.get("device", "")
        action = params.get("action", "")
        
        if not self.ha:
            return f"{action}了{device}（未连接HA）"
        
        # 转换为HA实体ID格式
        entity_id = f"switch.{device}"
        
        if action == "开":
            self.ha.turn_on(entity_id)
            return f"已打开{device}"
        else:
            self.ha.turn_off(entity_id)
            return f"已关闭{device}"
    
    def _handle_weather(self, params: Dict[str, Any]) -> str:
        """查询天气"""
        from .weather_service import get_weather_service
        weather_svc = get_weather_service()
        # 从参数中提取城市，默认北京
        city = params.get("city", "北京")
        return weather_svc.get_weather(city)
    
    def _handle_time(self, params: Dict[str, Any]) -> str:
        """查询时间"""
        from datetime import datetime
        now = datetime.now()
        return f"现在是{now.hour}点{now.minute}分"
    
    def _handle_chat(self, params: Dict[str, Any]) -> str:
        """闲聊/对话"""
        text = params.get("raw_text", "")
        
        if not self.llm:
            return "抱歉，我还没有接入大模型"
        
        # 调用LLM对话
        response = self.llm.chat(text)
        
        # 语音播报
        self.echo.speak(response)
        
        return response


class VoiceCommandProcessor:
    """语音命令处理器 - 整合意图识别和动作执行"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        # 初始化各个服务
        from .echo_service import EchoServiceController
        from .ha_service import HAService
        from .music_service import MusicService
        from .llm_service import LLMService
        
        # EchoService控制器
        device_ip = config.get("device_ip", "")
        self.echo = EchoServiceController(device_ip)
        
        # 其他服务
        self.ha = None
        self.music = None
        self.llm = None
        
        # 初始化意图识别和动作执行
        self.recognizer = IntentRecognizer()
        self.executor = ActionExecutor(
            echo_controller=self.echo,
            ha_service=self.ha,
            music_service=self.music,
            llm_service=self.llm
        )
    
    def process(self, text: str) -> str:
        """
        处理语音命令
        
        Args:
            text: 用户文本
            
        Returns:
            回复文本
        """
        # 1. 意图识别
        intent, params = self.recognizer.recognize(text)
        
        # 2. 动作执行
        response = self.executor.execute(intent, params)
        
        # 3. 语音播报
        self.echo.speak(response)
        
        return response
    
    def update_services(self, llm_service=None, ha_service=None, music_service=None):
        """更新服务实例"""
        self.llm = llm_service
        self.ha = ha_service
        self.music = music_service
        
        # 更新执行器
        self.executor = ActionExecutor(
            echo_controller=self.echo,
            ha_service=self.ha,
            music_service=self.music,
            llm_service=self.llm
        )
        self.recognizer.llm = llm_service
