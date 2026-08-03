# 斐讯R1智能控制中心 - Web版

部署在斐讯R1设备上的Web控制面板，通过浏览器访问管理。

## 功能特性

- 📱 **设备控制**: 截屏、点击、滑动、应用管理
- 🤖 **大模型对话**: 支持接入OpenAI API风格的LLM服务
- 🎵 **音乐播放**: 网易云音乐二维码登录、搜索、播放
- 🏠 **智能家居**: Home Assistant本地集成

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
        "enabled": false,
        "api_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-3.5-turbo"
    },
    "music": {
        "enabled": false,
        "source": "netEase",
        "cookie": ""
    },
    "home_assistant": {
        "enabled": false,
        "url": "http://192.168.1.x:8123",
        "token": ""
    }
}
```

## 页面说明

| 路径 | 说明 |
|------|------|
| `/` | 首页/控制面板 |
| `/settings` | 配置页面 |
| `/music` | 音乐播放 |
| `/ha` | 智能家居控制 |
| `/chat` | AI对话 |

## 项目结构

```
R1_Controller/
├── main.py                 # 主入口
├── config/
│   └── config_manager.py  # 配置管理
├── modules/
│   ├── adb_helper.py     # ADB控制
│   ├── llm_service.py    # 大模型
│   ├── music_service.py  # 音乐服务
│   └── ha_service.py     # Home Assistant
├── app/
│   ├── __init__.py       # FastAPI应用
│   ├── api/              # API路由
│   │   ├── device.py
│   │   ├── llm.py
│   │   ├── music.py
│   │   ├── ha.py
│   │   └── config.py
│   └── web/
│       └── templates/    # HTML模板
│           ├── index.html
│           ├── settings.html
│           ├── music.html
│           ├── ha.html
│           └── chat.html
└── requirements.txt
```

## 许可证

MIT License
