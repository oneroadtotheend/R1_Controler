#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Home Assistant 服务
"""

import requests


class HAService:
    """Home Assistant服务类"""

    def __init__(self, config):
        self.config = config

    def get_states(self):
        """获取所有状态"""
        url = self.config.get("home_assistant.url")
        token = self.config.get("home_assistant.token")

        if not url or not token:
            return []

        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(
                f"{url}/api/states",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass

        return []

    def get_entities(self, domain=None):
        """获取实体"""
        states = self.get_states()
        if domain:
            return [s for s in states if s['entity_id'].startswith(f"{domain}.")]
        return states

    def call_service(self, domain, service, entity_id=None, data=None):
        """调用服务"""
        url = self.config.get("home_assistant.url")
        token = self.config.get("home_assistant.token")

        if not url or not token:
            return False, "配置错误"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = data or {}
        if entity_id:
            payload["entity_id"] = entity_id

        try:
            response = requests.post(
                f"{url}/api/services/{domain}/{service}",
                headers=headers,
                json=payload,
                timeout=10
            )
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            return False, str(e)

    def turn_on(self, entity_id):
        """打开"""
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "turn_on", entity_id)

    def turn_off(self, entity_id):
        """关闭"""
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "turn_off", entity_id)

    def toggle(self, entity_id):
        """切换"""
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "toggle", entity_id)

    def is_configured(self):
        """检查是否已配置"""
        url = self.config.get("home_assistant.url")
        token = self.config.get("home_assistant.token")
        return bool(url and token)

    def test_connection(self):
        """测试连接"""
        url = self.config.get("home_assistant.url")
        token = self.config.get("home_assistant.token")

        if not url or not token:
            return False

        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(f"{url}/api/", headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
