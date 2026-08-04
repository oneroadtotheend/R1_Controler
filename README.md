# 斐讯R1智能控制中心 - Web版

部署在斐讯R1设备上的Web控制面板，通过浏览器访问管理。

## 功能特性

- 📱 **设备控制**: 截屏、点击、滑动、应用管理
- 🤖 **大模型对话**: 支持接入 OpenAI/MiniMax API 风格的大模型服务
- 🎵 **音乐播放**: 网易云音乐二维码登录、搜索、播放
- 🏠 **智能家居**: Home Assistant 本地集成
- 🎙️ **语音控制**: 语音命令识别，支持天气查询、音乐播放、设备控制
- 🌤️ **天气查询**: 自动获取用户 IP 定位城市，查询实时天气
- 📊 **服务监控**: 自动检测服务状态，支持自动重启

## 技术架构

```
前端: Bootstrap 5 + Jinja2模板
后端: FastAPI (Python)
```

## 运行方式

### 1. 在电脑上测试运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 访问 http://localhost:8080
```

### 2. 部署到斐讯R1

方式一：直接运行Python
```bash
pip install -r requirements.txt
python main.py
```

方式二：打包成APK (推荐)

需要使用 Buildozer:

```bash
# 安装 Buildozer
pip install buildozer

# 初始化
buildozer init

# 打包
buildozer android debug
```

## 配置说明

配置文件位于 `config/settings.json`:

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8080
    },
    "llm": {
        "enabled": true,
        "api_url": "https://api.minimaxi.com/v1",
        "api_key": "your-api-key",
        "model": "MiniMax-M3"
    },
    "music": {
        "enabled": true,
        "source": "netEase",
        "local_api_url": "http://192.168.x.x:3000",
        "qrcode_login": true
    },
    "home_assistant": {
        "enabled": false,
        "url": "http://192.168.1.x:8123",
        "token": "your-ha-token"
    }
}
```

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `llm.api_url` | 大模型 API 地址（支持 OpenAI 兼容接口） |
| `llm.api_key` | 大模型 API Key |
| `music.local_api_url` | 网易云音乐 API 地址（需要自行部署） |
| `home_assistant.url` | Home Assistant 服务地址 |
| `home_assistant.token` | Home Assistant 长期访问令牌 |

## 页面说明

| 路径 | 说明 |
|------|------|
| `/` | 首页/控制面板 |
| `/settings` | 配置页面 |
| `/music` | 音乐播放 |
| `/ha` | 智能家居控制 |
| `/chat` | AI 对话 |

## API 接口

### 语音控制

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/voice/command` | 处理语音命令 |
| POST | `/api/voice/echo/play` | 播放音乐 |
| POST | `/api/voice/echo/pause` | 暂停播放 |
| POST | `/api/voice/echo/volume/up` | 增加音量 |
| POST | `/api/voice/echo/volume/down` | 减少音量 |
| POST | `/api/voice/echo/speak` | 语音播报 |

### 大模型

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/llm/chat` | AI 对话（支持天气自动查询） |
| GET | `/api/llm/status` | 获取 LLM 服务状态 |

### 音乐服务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/music/status` | 获取音乐服务状态 |
| GET | `/api/music/qrcode` | 获取登录二维码 |
| POST | `/api/music/login` | 确认二维码登录 |
| GET | `/api/music/playlist` | 获取播放列表 |
| POST | `/api/music/play` | 播放歌曲 |
| POST | `/api/music/pause` | 暂停播放 |

### 智能家居

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ha/status` | 获取 HA 服务状态 |
| GET | `/api/ha/states` | 获取所有实体状态 |
| POST | `/api/ha/control` | 控制实体 |

### 服务监控

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/monitor/status` | 获取监控状态 |
| POST | `/api/monitor/restart` | 重启服务 |

## 语音命令示例

- "播放音乐" / "播放周杰伦的歌"
- "暂停" / "继续"
- "下一首" / "上一首"
- "声音大一点" / "声音小一点"
- "今天天气怎么样"
- "开灯" / "关灯"（需要 Home Assistant）

## 项目结构

```
R1_Controller/
├── main.py                      # 主入口
├── buildozer.spec              # APK 打包配置
├── config/
│   ├── config_manager.py       # 配置管理
│   └── settings.json          # 配置文件
├── modules/
│   ├── adb_helper.py          # ADB 控制
│   ├── llm_service.py         # 大模型服务
│   ├── music_service.py       # 网易云音乐
│   ├── ha_service.py          # Home Assistant
│   ├── echo_service.py        # EchoService 控制
│   ├── voice_processor.py     # 语音命令处理
│   ├── weather_service.py     # 天气查询
│   ├── unisound_integration.py # 云知声集成
│   └── service_monitor.py     # 服务监控
├── app/
│   ├── __init__.py           # FastAPI 应用
│   ├── api/                  # API 路由
│   │   ├── device.py
│   │   ├── llm.py
│   │   ├── music.py
│   │   ├── ha.py
│   │   ├── voice.py
│   │   └── config.py
│   └── web/
│       └── templates/        # HTML 模板
│           ├── index.html
│           ├── settings.html
│           ├── music.html
│           ├── ha.html
│           └── chat.html
└── requirements.txt
```

## 许可证

MIT License
