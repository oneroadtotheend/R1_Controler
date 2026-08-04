# 斐讯R1智能控制中心 - 项目梳理

> 梳理时间: 2026-08-03

## 一、项目定位

部署在**斐讯R1智能音箱**（Android设备, RK3229, ARMv7）上的 Web 控制面板，通过浏览器访问管理。支持两种运行模式：

- **PC模式**: 直接 `python main.py`，uvicorn 起服务，浏览器访问 `http://localhost:8080`
- **Android模式(APK)**: Kivy WebView 内嵌浏览器加载本地 FastAPI 服务（通过 Buildozer 打包）

## 二、技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python FastAPI + Uvicorn |
| 前端 | HTML/CSS/JS (Bootstrap 5) + Jinja2模板 |
| 设备控制 | ADB (subprocess 调用) |
| AI | OpenAI API 格式 (当前用 MiniMax M3) |
| 音乐 | 网易云音乐 API (本地部署 192.168.50.81:3000) |
| 家居 | Home Assistant REST API |
| 打包 | Buildozer + Kivy (APK) |

## 三、代码结构

```
R1_Controller/
├── main.py                          # 入口：PC模式(uvicorn) / Android模式(Kivy WebView)
├── config/
│   ├── config_manager.py            # JSON配置管理，支持点号取值 get("server.host")
│   └── settings.json                # 运行时配置（含API Key，注意安全）
├── app/
│   ├── __init__.py                  # FastAPI应用工厂，注册6个API路由+7个页面路由
│   ├── api/                         # REST API 路由
│   │   ├── device.py                # /api/device - 设备连接/截屏/点击/滑动/应用管理
│   │   ├── llm.py                   # /api/llm - 大模型对话/意图分析
│   │   ├── music.py                 # /api/music - 网易云搜索/播放/歌单/二维码登录
│   │   ├── ha.py                    # /api/ha - Home Assistant设备控制
│   │   ├── voice.py                 # /api/voice - 语音命令处理+EchoService控制
│   │   └── config.py                # /api/config - 配置读写
│   └── web/templates/               # HTML页面
│       ├── index.html               # 首页/控制面板
│       ├── settings.html            # 配置页面
│       ├── music.html               # 音乐播放
│       ├── ha.html                  # 智能家居
│       ├── chat.html                # AI对话
│       ├── voice.html               # 语音控制
│       └── monitor.html             # 服务监控
├── modules/                         # 业务模块
│   ├── adb_helper.py                # ADB设备控制（连接/截屏/点击/滑动/按键/应用管理）
│   ├── llm_service.py               # 大模型服务（chat + analyze_intent）
│   ├── music_service.py             # 网易云音乐（QR登录/搜索/播放URL/歌单）
│   ├── ha_service.py                # Home Assistant（状态查询/服务调用/开关）
│   ├── echo_service.py              # EchoService控制（播放/暂停/TTS，通过ADB广播）
│   │                                #   + VoiceAssistant类（整合LLM+Echo+HA的语音助手）
│   ├── voice_processor.py           # 语音指令处理（IntentRecognizer + ActionExecutor + VoiceCommandProcessor）
│   ├── service_monitor.py           # 服务监控（云知声/EchoService状态检测/自动重启/内存清理）
│   └── unisound_integration.py      # 云知声集成（UnisoundService + R1VoiceController，大部分为空实现）
├── buildozer.spec                   # APK打包配置（armeabi-v7a, min API 21, target API 29）
├── requirements.txt                 # Python依赖
├── ARCHITECTURE.md                  # 架构文档
└── README.md                        # 项目说明
```

## 四、当前配置状态

| 服务 | 状态 | 说明 |
|------|------|------|
| LLM | ✅ 已启用 | MiniMax M3, api.minimaxi.com |
| Music | ✅ 已启用 | 网易云, 本地API 192.168.50.81:3000 |
| Home Assistant | ❌ 未启用 | 需配置URL和Token |

## 五、数据流概览

1. **设备控制**: 浏览器 → FastAPI → ADBHelper → `adb shell` 命令 → R1设备
2. **音乐播放**: 浏览器 → FastAPI → MusicService → 网易云本地API → 返回歌曲URL → 浏览器 `<audio>` 播放
3. **AI对话**: 浏览器 → FastAPI → LLMService → MiniMax API → 返回回复
4. **语音命令**: 浏览器 → FastAPI → VoiceCommandProcessor → 意图识别(关键词/LLM) → 动作执行(EchoService/HA/Music) → TTS播报
5. **服务监控**: FastAPI → R1ServiceMonitor → ADB shell(ps/dumpsys) → 状态检测/自动重启

## 六、已知问题 & 待修复项

### Bug（会导致运行时错误）

1. **voice_processor.py 类名导入不匹配**
   - `VoiceCommandProcessor.__init__` 中 `from .ha_service import HomeAssistantService`，但实际类名是 `HAService`
   - `EchoServiceController` 的构造函数接收 `device_ip` 字符串，但代码传入的是 config dict

2. **LLMService / HAService 缺少 `is_configured()` 方法**
   - `unisound_integration.py` 中的 `R1VoiceController` 调用了 `self.llm.is_configured()` 和 `self.ha.is_configured()`，但这两个类没有此方法

3. **voice.py API 每次请求新建 EchoServiceController 实例**
   - `/api/voice/echo/*` 系列接口每次都 `EchoServiceController(device_ip)` 新建实例
   - 应复用 `app.state.echo` 中已初始化的实例

### 未完成功能

4. **unisound_integration.py 全为空实现**
   - `start_unisound()`, `stop_unisound()`, `trigger_wakeup()`, `send_voice_text()`, `get_tts_audio()` 全是 `pass`
   - ARCHITECTURE.md 中列出的待实现功能均未开始

5. **天气查询为硬编码**
   - `voice_processor.py` 和 `echo_service.py` 中的天气响应都是 `"今天天气晴朗，温度25度"`

### 安全问题

6. **settings.json 暴露 API Key**
   - `api_key` 明文存储在 `config/settings.json` 中
   - 建议改为环境变量读取或至少加入 `.gitignore`

### 代码质量

7. **大量裸 `except:` 吞异常**
   - `ha_service.py`, `music_service.py`, `voice_processor.py` 等多处 `except:` 或 `except Exception` 后直接 `pass` 或 `return False`
   - 建议至少记录日志

8. **ARCHITECTURE.md 与代码不一致**
   - 文档中配置文件路径写的是 `config/config.json`，实际是 `config/settings.json`
   - 文档中 `ha_service` 的类描述与实际不一致

## 七、明天开发建议优先级

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 修复 voice_processor.py 导入错误 | 否则语音命令功能完全不可用 |
| P0 | 添加 is_configured() 方法 | LLMService 和 HAService 各加一个 |
| P1 | voice.py 复用 app.state.echo | 避免每次请求新建实例 |
| P1 | settings.json 加入 .gitignore | API Key 安全 |
| P2 | 实现天气查询 | 接入免费天气API |
| P2 | unisound_integration 实现启动/停止 | 至少完成基础服务控制 |
| P3 | 异常处理规范化 | 统一日志记录 |
| P3 | ARCHITECTURE.md 同步更新 | 文档与代码保持一致 |

## 八、关键代码入口

- **启动服务**: `python main.py` → `run_pc()` → `uvicorn.run(app, host, port)`
- **应用工厂**: `app/__init__.py` → `create_app(config)` → 注册路由 + 初始化服务
- **配置读取**: `config.get("llm.api_url")` → 点号分隔递归查找
- **ADB连接**: `POST /api/device/connect?ip=192.168.x.x` → `ADBHelper.connect(ip)`
- **语音命令**: `POST /api/voice/command` → `VoiceCommandProcessor.process(text)` → 意图识别 + 动作执行
