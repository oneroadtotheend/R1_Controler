#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐服务 - 支持本地API和网易云音乐
"""

import requests
import json
import time
import random
import base64
import os


class MusicService:
    """音乐服务类"""

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36",
            "Referer": "https://music.163.com/"
        })
        self.cookie = None

    def _get_api_url(self):
        """获取API地址"""
        # 优先使用本地API
        local_url = self.config.get("music.local_api_url", "")
        if local_url:
            return local_url.rstrip('/')
        # 默认官方API
        return "https://netease-cloud-music-api-five-roan-25.vercel.app"

    def get_qrcode(self):
        """获取二维码 - 使用本地API"""
        api_url = self._get_api_url()

        try:
            # 调用登录二维码接口
            response = self.session.get(
                f"{api_url}/login/qr/key",
                params={"timestamp": int(time.time())},
                timeout=10
            )
            data = response.json()

            if data.get("code") == 200:
                unikey = data.get("data", {}).get("unikey")
                # 生成二维码链接
                qrurl = f"https://music.163.com/login?codekey={unikey}&type=1"
                return {"unikey": unikey, "qrurl": qrurl}
        except Exception as e:
            print(f"获取二维码失败: {e}")

        # 降级方案
        unikey = f"music_{int(time.time() * 1000)}{random.randint(1000, 9999)}"
        qrurl = f"https://music.163.com/login?codekey={unikey}&type=1"
        return {"unikey": unikey, "qrurl": qrurl}

    def check_qrcode_status(self, unikey):
        """检查二维码状态"""
        api_url = self._get_api_url()

        try:
            response = self.session.get(
                f"{api_url}/login/qr/check",
                params={"key": unikey, "timestamp": int(time.time())},
                timeout=10
            )
            data = response.json()

            code = data.get("code", -1)
            if code == 803:  # 登录成功
                return "SUCCESS"
            elif code == 800:  # 二维码过期
                return "EXPIRED"
            elif code == 801:  # 等待扫码
                return "WAITING"
            elif code == 802:  # 已扫码待确认
                return "SCAN"
        except Exception as e:
            print(f"检查二维码状态失败: {e}")

        return "TIMEOUT"

    def login_with_cookie(self, cookie_str):
        """Cookie登录"""
        self.cookie = cookie_str
        for item in cookie_str.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                self.session.cookies.set(key, value)

        # 验证Cookie
        try:
            api_url = self._get_api_url()
            response = self.session.get(
                f"{api_url}/user/account",
                timeout=10
            )
            data = response.json()
            return data.get('code') == 200
        except:
            return False

    def search(self, keyword, source="netEase"):
        """搜索音乐"""
        api_url = self._get_api_url()

        try:
            response = self.session.get(
                f"{api_url}/search",
                params={"keywords": keyword, "type": 1, "limit": 20},
                timeout=10
            )
            data = response.json()

            songs = []
            if data.get('result', {}).get('songs'):
                for song in data['result']['songs']:
                    artists = song.get('ar', [])
                    artist_name = ", ".join([a.get('name', '') for a in artists])

                    songs.append({
                        'id': song.get('id'),
                        'name': song.get('name'),
                        'artist': artist_name,
                        'album': song.get('ar', [{}])[0].get('name', '') if song.get('ar') else '',
                        'duration': song.get('dt', 0) // 1000,
                        'source': 'netEase'
                    })

            return songs
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def get_play_url(self, song_id):
        """获取播放地址"""
        api_url = self._get_api_url()

        try:
            # 获取歌曲详情
            response = self.session.get(
                f"{api_url}/song/url",
                params={"id": song_id, "br": 320000},
                timeout=10
            )
            data = response.json()

            if data.get('data'):
                song_data = data['data'][0]
                return {
                    'url': song_data.get('url', ''),
                    'br': song_data.get('br', 0),
                    'size': song_data.get('size', 0)
                }
        except Exception as e:
            print(f"获取播放地址失败: {e}")

        return None

    def get_playlist(self, playlist_id):
        """获取歌单详情"""
        api_url = self._get_api_url()

        try:
            response = self.session.get(
                f"{api_url}/playlist/detail",
                params={"id": playlist_id},
                timeout=10
            )
            data = response.json()

            if data.get('playlist', {}).get('tracks'):
                tracks = data['playlist']['tracks']
                songs = []
                for song in tracks:
                    artists = song.get('ar', [])
                    artist_name = ", ".join([a.get('name', '') for a in artists])

                    songs.append({
                        'id': song.get('id'),
                        'name': song.get('name'),
                        'artist': artist_name,
                        'album': song.get('al', {}).get('name', ''),
                        'source': 'netEase'
                    })
                return songs
        except Exception as e:
            print(f"获取歌单失败: {e}")

        return []

    def get_favorite_list(self):
        """获取我喜欢歌单"""
        api_url = self._get_api_url()

        try:
            # 获取用户歌单
            response = self.session.get(
                f"{api_url}/user/playlist",
                params={"uid": 0},  # 0表示当前用户
                timeout=10
            )
            data = response.json()

            if data.get('playlist'):
                # 找到"我喜欢"歌单
                for playlist in data['playlist']:
                    if playlist.get('name') == '我喜欢的音乐':
                        return self.get_playlist(playlist.get('id'))
        except Exception as e:
            print(f"获取喜欢歌单失败: {e}")

        return []
