#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气服务 - 使用 Open-Meteo 免费 API

特性：
- 无需 API Key
- 免费商用（非商业用途每日 10000 次）
- 全球覆盖
"""

import requests
from typing import Optional, Dict, Any


class WeatherService:
    """天气服务类"""

    # Open-Meteo API 端点
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    # IP 定位 API (免费，无需 Key)
    IP_API_URL = "http://ip-api.com/json/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "R1-Controller/1.0"
        })

    def get_city_by_ip(self, ip: str = None) -> Optional[str]:
        """
        通过 IP 地址获取城市名

        Args:
            ip: IP 地址，为空则自动获取本机 IP

        Returns:
            城市名称，失败返回 None
        """
        try:
            url = self.IP_API_URL
            if ip:
                url += ip

            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    # 优先使用中文城市名
                    city = data.get("city", "")
                    if not city:
                        city = data.get("country", "")
                    return city if city else None
            return None
        except Exception:
            return None

    def get_weather(self, city: str = None, ip: str = None) -> str:
        """
        获取天气信息

        Args:
            city: 城市名称（中文或英文），为空则自动通过 IP 定位
            ip: 指定 IP 地址进行定位，为空则自动获取

        Returns:
            格式化的天气描述字符串
        """
        try:
            # 如果没有指定城市，尝试通过 IP 自动获取
            if not city:
                city = self.get_city_by_ip(ip)
                if not city:
                    city = "北京"  # 默认城市

            # 1. 城市名转经纬度
            coords = self._geocoding(city)
            if not coords:
                return f"未找到城市 {city}，请检查名称是否正确"

            # 2. 获取天气数据
            weather = self._get_weather_data(coords["lat"], coords["lon"])
            if not weather:
                return "获取天气数据失败，请稍后重试"

            # 3. 格式化输出
            return self._format_weather(weather, city)

        except Exception as e:
            return f"查询天气失败: {str(e)}"

    def _geocoding(self, city: str) -> Optional[Dict[str, float]]:
        """城市名转经纬度"""
        try:
            # 尝试中文城市名
            params = {"name": city, "count": 1, "language": "zh", "format": "json"}
            resp = self.session.get(self.GEOCODING_URL, params=params, timeout=10)

            if resp.status_code != 200:
                return None

            data = resp.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                return {
                    "lat": result["latitude"],
                    "lon": result["longitude"],
                    "name": result.get("name", city)
                }

            # 中文找不到，试试英文（去掉中文）
            params = {"name": city.encode('utf-8').decode('unicode_escape'), "count": 1, "format": "json"}
            resp = self.session.get(self.GEOCODING_URL, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "results" in data and len(data["results"]) > 0:
                    result = data["results"][0]
                    return {
                        "lat": result["latitude"],
                        "lon": result["longitude"],
                        "name": result.get("name", city)
                    }

            return None

        except Exception:
            return None

    def _get_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """获取天气数据"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
            "forecast_days": 3
        }

        try:
            resp = self.session.get(self.WEATHER_URL, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def _format_weather(self, data: Dict[str, Any], city: str) -> str:
        """格式化天气输出"""
        try:
            current = data.get("current", {})
            daily = data.get("daily", {})

            # 天气代码转中文
            weather_code = current.get("weather_code", 0)
            weather_desc = self._weather_code_to_chinese(weather_code)

            # 温度
            temp = current.get("temperature_2m", 0)
            humidity = current.get("relative_humidity_2m", 0)
            wind_speed = current.get("wind_speed_10m", 0)

            # 今日高低温度
            if daily.get("temperature_2m_max"):
                temp_max = daily["temperature_2m_max"][0]
                temp_min = daily["temperature_2m_min"][0]
                temp_range = f"{temp_min}°C ~ {temp_max}°C"
            else:
                temp_range = f"{temp}°C"

            # 构造回复 - 直接使用传入的城市名
            location = city

            result = f"{location}当前{weather_desc}，"
            result += f"气温{temp}度，"
            result += f"湿度{int(humidity)}%，"
            result += f"风速{int(wind_speed)}公里/小时。"

            # 如果有未来两天预报
            if len(daily.get("weather_code", [])) > 1:
                tomorrow_code = daily["weather_code"][1]
                tomorrow_temp_max = daily["temperature_2m_max"][1]
                tomorrow_temp_min = daily["temperature_2m_min"][1]
                tomorrow_desc = self._weather_code_to_chinese(tomorrow_code)
                result += f"明天{tomorrow_desc}，气温{tomorrow_temp_min}°C ~ {tomorrow_temp_max}°C。"

            return result

        except Exception as e:
            return f"天气数据解析失败: {str(e)}"

    def _weather_code_to_chinese(self, code: int) -> str:
        """WMO 天气代码转中文"""
        weather_map = {
            0: "晴",
            1: "晴间多云",
            2: "多云",
            3: "阴",
            45: "雾",
            48: "雾凇",
            51: "小毛毛雨",
            53: "中毛毛雨",
            55: "大毛毛雨",
            56: "冻毛毛雨",
            57: "强冻毛毛雨",
            61: "小雨",
            63: "中雨",
            65: "大雨",
            66: "小冻雨",
            67: "大冻雨",
            71: "小雪",
            73: "中雪",
            75: "大雪",
            77: "雪粒",
            80: "小阵雨",
            81: "中阵雨",
            82: "大阵雨",
            85: "小阵雪",
            86: "大阵雪",
            95: "雷暴",
            96: "雷暴加小冰雹",
            99: "雷暴加大冰雹",
        }
        return weather_map.get(code, f"天气代码{code}")


# 全局单例
_weather_service = None


def get_weather_service() -> WeatherService:
    """获取天气服务单例"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
