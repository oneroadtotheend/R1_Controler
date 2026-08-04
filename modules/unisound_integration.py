#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斐讯R1智能音箱 - 整合云知声方案

架构设计:
┌─────────────────────────────────────────────────────────────────┐
│                      斐讯R1设备 (Android)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              云知声语音服务 (unisound APK)                │  │
│  │  • 唤醒词检测                                              │  │
│  │  • 语音识别 (ASR)                                         │  │
│  │  • 语义理解 (NLU)                                         │  │
│  │  • 语音合成 (TTS)                                         │  │
│  │  • 技能执行 (音乐/天气/家居/聊天)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ ADB/广播/服务调用                  │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              R1_Controller Web服务                         │  │
│  │  • FastAPI 后端                                           │  │
│  │  • Web管理界面                                            │  │
│  │  • 大模型接入                                             │  │
│  │  • 网易云音乐                                             │  │
│  │  • HomeAssistant                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                         ▲
                         │ 浏览器访问
                         │
┌─────────────────────────────────────────────────────────────────┐
│                      用户设备 (手机/电脑)                        │
└─────────────────────────────────────────────────────────────────┘
"""

# ========== 云知声服务集成 ==========

class UnisoundService:
    """云知声服务集成"""
    
    # APK包名
    PACKAGE_NAME = "com.unisound.vui"  # 需要确认实际包名
    
    # 斐讯定制版包名
    PHICOMM_PACKAGE = "com.phicomm.speaker.player"  # EchoService
    
    def __init__(self, device_ip: str = None):
        self.device_ip = device_ip
        # 延迟导入避免循环依赖
        from modules.adb_helper import ADBHelper
        self.adb = ADBHelper(device_ip) if device_ip else None

    def start_unisound(self) -> bool:
        """启动云知声服务"""
        if not self.adb:
            return False
        try:
            # 启动云知声主Activity
            # com.unisound.vui 是云知声主包（需确认实际包名）
            # 这里用 phicomm 的包名尝试
            self.adb.shell("am start -n com.phicomm.speaker.player/com.phicomm.speaker.player.ui.MainActivity")
            return True
        except Exception:
            return False

    def stop_unisound(self) -> bool:
        """停止云知声服务"""
        if not self.adb:
            return False
        try:
            # 强制停止云知声应用
            self.adb.shell("am force-stop com.phicomm.speaker.player")
            return True
        except Exception:
            return False

    def trigger_wakeup(self) -> bool:
        """触发一次唤醒（模拟唤醒词）"""
        if not self.adb:
            return False
        try:
            # 发送广播模拟唤醒词
            self.adb.shell("am broadcast -a com.unisound.vui.wakeup -e wakeup '小飞小飞'")
            return True
        except Exception:
            return False

    def send_voice_text(self, text: str) -> str:
        """发送文本进行语音识别和处理

        这是一个简化的接口，直接发送文本让云知声处理
        注：云知声主要接收语音输入，此方法用于调试或测试
        """
        # 可通过广播发送文本（取决于云知声是否支持）
        if not self.adb:
            return "设备未连接"
        try:
            self.adb.shell(f"am broadcast -a com.unisound.vui.asr --es text '{text}'")
            return "已发送文本到语音识别"
        except Exception as e:
            return f"发送失败: {str(e)}"

    def get_tts_audio(self, text: str) -> bytes:
        """获取TTS音频"""
        # 云知声 TTS 需要调用其 SDK，此处返回空
        # 实际项目可使用其他 TTS 服务
        return b""


# ========== 整合后的语音控制器 ==========

class R1VoiceController:
    """R1语音控制器 - 整合云知声 + R1_Controller"""
    
    def __init__(self, config: dict):
        # 云知声服务
        self.unisound = UnisoundService(config.get("device_ip"))
        
        # R1_Controller服务
        from modules.llm_service import LLMService
        from modules.music_service import MusicService
        from modules.ha_service import HAService
        from modules.adb_helper import ADBHelper
        
        self.llm = LLMService(config)
        self.music = MusicService(config)
        self.ha = HAService(config)
        self.adb = ADBHelper()
        
    def handle_voice_input(self, text: str) -> str:
        """处理语音输入
        
        流程:
        1. 发送到云知声处理 (NLU意图识别)
        2. 根据意图调用对应服务
        3. 返回结果并语音播报
        """
        # 1. 意图识别 - 可以用云知声也可以用LLM
        intent = self._recognize_intent(text)
        
        # 2. 执行动作
        response = self._execute_intent(intent, text)
        
        # 3. 语音播报
        self._speak(response)
        
        return response
    
    def _recognize_intent(self, text: str) -> str:
        """意图识别"""
        # 优先使用LLM
        if self.llm.is_configured():
            prompt = f"""识别用户意图，只返回意图类型。
            
用户说: {text}

意图类型: 播放音乐, 暂停, 继续, 下一首, 上一首, 音量加, 音量减, 开灯, 关灯, 查询天气, 查询时间, 闲聊

只返回意图类型，不要其他内容。"""
            result = self.llm.chat(prompt)
            return result.strip()
        else:
            # fallback到关键词匹配
            return self._keyword_match(text)
    
    def _keyword_match(self, text: str) -> str:
        """关键词匹配"""
        keywords = {
            "播放音乐": ["播放", "听", "放首歌"],
            "暂停": ["暂停", "停止"],
            "继续": ["继续", "接着放"],
            "下一首": ["下一首", "切歌"],
            "音量加": ["大声点", "声音大"],
            "音量减": ["小声点", "声音小"],
            "开灯": ["开灯", "打开灯"],
            "关灯": ["关灯", "关闭灯"],
            "查询天气": ["天气"],
            "查询时间": ["几点", "时间"],
        }
        
        for intent, words in keywords.items():
            for word in words:
                if word in text:
                    return intent
        return "闲聊"
    
    def _execute_intent(self, intent: str, text: str) -> str:
        """执行意图"""
        if intent == "播放音乐":
            # 提取歌曲名
            keyword = text.replace("播放", "").replace("听", "").strip()
            if keyword:
                # 调用音乐服务搜索播放
                return f"好的，播放{keyword}"
            else:
                # 播放默认列表
                return "好的，播放音乐"
                
        elif intent == "暂停":
            self.adb.shell("input keyevent 85")  # 播放/暂停
            return "已暂停"
            
        elif intent == "继续":
            self.adb.shell("input keyevent 85")
            return "继续播放"
            
        elif intent == "下一首":
            self.adb.shell("input keyevent 87")
            return "切换到下一首"
            
        elif intent == "上一首":
            self.adb.shell("input keyevent 88")
            return "切换到上一首"
            
        elif intent == "音量加":
            self.adb.shell("input keyevent 24")
            return "音量已增加"
            
        elif intent == "音量减":
            self.adb.shell("input keyevent 25")
            return "音量已减小"
            
        elif intent == "开灯":
            if self.ha.is_configured():
                self.ha.turn_on("light")
            return "已打开灯光"
            
        elif intent == "关灯":
            if self.ha.is_configured():
                self.ha.turn_off("light")
            return "已关闭灯光"
            
        elif intent == "查询天气":
            from .weather_service import get_weather_service
            weather_svc = get_weather_service()
            return weather_svc.get_weather("北京")
            
        elif intent == "查询时间":
            from datetime import datetime
            now = datetime.now()
            return f"现在是{now.hour}点{now.minute}分"
            
        elif intent == "闲聊":
            if self.llm.is_configured():
                return self.llm.chat(text)
            return "你好，我是斐讯R1智能音箱"
            
        return "好的"
    
    def _speak(self, text: str) -> bool:
        """语音播报"""
        # 方式1: 通过ADB调用TTS
        # self.adb.shell(f"am broadcast -a com.unisound.vui.tts --es text '{text}'")
        
        # 方式2: 使用云知声TTS
        # audio = self.unisound.get_tts_audio(text)
        # 播放音频
        
        return True


# ========== Web API 整合 ==========

"""
在R1_Controller中添加语音控制接口:

POST /api/voice/unisound/start    - 启动云知声服务
POST /api/voice/unisound/stop     - 停止云知声服务  
POST /api/voice/process            - 处理语音输入
GET  /api/voice/status             - 获取语音服务状态
"""
