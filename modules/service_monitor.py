#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斐讯R1服务监控模块

功能:
- 监控云知声/EchoService服务状态
- 自动检测服务是否卡住
- 自动重启服务
- 内存监控和清理
- 日志记录
"""

import time
import threading
import subprocess
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum


class ServiceStatus(Enum):
    """服务状态"""
    RUNNING = "running"
    NOT_RUNNING = "not_running"
    UNRESPONSIVE = "unresponsive"
    UNKNOWN = "unknown"


class R1ServiceMonitor:
    """R1服务监控器"""
    
    # 要监控的服务
    SERVICES = {
        "unisound": {
            "package": "com.unisound.vui",
            "name": "云知声语音服务",
            "process_name": "unisound"
        },
        "echo_service": {
            "package": "com.phicomm.speaker.player", 
            "name": "EchoService",
            "process_name": "speaker.player"
        },
        "mediaserver": {
            "package": "android",
            "name": "媒体服务",
            "process_name": "mediaserver"
        }
    }
    
    def __init__(self, device_ip: str = None, adb_helper=None):
        """
        初始化监控器
        
        Args:
            device_ip: R1的IP地址
            adb_helper: ADBHelper实例
        """
        self.device_ip = device_ip
        self.adb = adb_helper
        
        # 监控配置
        self.check_interval = 60  # 检查间隔(秒)
        self.unresponsive_threshold = 3  # 无响应次数阈值
        self.memory_threshold = 200 * 1024 * 1024  # 内存阈值 200MB
        
        # 状态
        self._running = False
        self._monitor_thread = None
        self._callbacks = []
        self._service_status = {}  # 各服务状态
        self._unresponsive_count = {}  # 无响应计数
        
        # 日志
        self._log = []
        
    def _run_shell(self, command: str) -> str:
        """执行ADB shell命令"""
        # 构建ADB命令
        if self.device_ip:
            cmd = f"adb -s {self.device_ip}:5555 shell {command}"
        elif self.adb and hasattr(self.adb, 'device_ip') and self.adb.device_ip:
            cmd = f"adb -s {self.adb.device_ip}:5555 shell {command}"
        else:
            cmd = f"adb shell {command}"
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.stdout
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            return ""
    
    # ========== 服务状态检测 ==========
    
    def get_service_status(self, service_name: str) -> ServiceStatus:
        """
        获取服务状态
        
        Args:
            service_name: 服务名称 (unisound/echo_service/mediaserver)
            
        Returns:
            ServiceStatus
        """
        service = self.SERVICES.get(service_name)
        if not service:
            return ServiceStatus.UNKNOWN
            
        # 检查进程是否在运行
        process_name = service["process_name"]
        cmd = f"ps -A | grep {process_name}"
        result = self._run_shell(cmd)
        
        if process_name in result:
            # 进程在运行，进一步检查是否响应
            if self._check_responsive(service_name):
                return ServiceStatus.RUNNING
            else:
                return ServiceStatus.UNRESPONSIVE
        else:
            return ServiceStatus.NOT_RUNNING
    
    def _check_responsive(self, service_name: str) -> bool:
        """检查服务是否响应"""
        # 尝试获取服务状态
        try:
            if service_name == "unisound":
                # 检查云知声服务是否能响应
                # 可以通过检查某个关键文件或日志
                cmd = "logcat -d -t 1 -s Unisound:* 2>/dev/null | head -1"
            elif service_name == "echo_service":
                # 检查EchoService
                cmd = "dumpsys activity service com.phicomm.speaker.player 2>/dev/null | head -5"
            else:
                return True  # 默认认为响应
                
            result = self._run_shell(cmd)
            return len(result) > 0
        except:
            return False
    
    def get_all_services_status(self) -> Dict[str, ServiceStatus]:
        """获取所有服务状态"""
        status = {}
        for name in self.SERVICES:
            status[name] = self.get_service_status(name)
        return status
    
    # ========== 服务控制 ==========
    
    def restart_service(self, service_name: str) -> bool:
        """
        重启服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            是否成功
        """
        service = self.SERVICES.get(service_name)
        if not service:
            return False
            
        package = service["package"]
        self._log_event(f"正在重启服务: {service['name']}")
        
        try:
            # 强制停止服务
            cmd = f"am force-stop {package}"
            self._run_shell(cmd)
            time.sleep(1)
            
            # 启动服务
            cmd = f"am startservice -n {package}/.MainActivity"
            self._run_shell(cmd)
            time.sleep(2)
            
            # 检查是否启动成功
            if self.get_service_status(service_name) == ServiceStatus.RUNNING:
                self._log_event(f"✓ 服务重启成功: {service['name']}")
                return True
            else:
                self._log_event(f"✗ 服务重启失败: {service['name']}")
                return False
                
        except Exception as e:
            self._log_event(f"✗ 重启服务出错: {e}")
            return False
    
    def restart_all_services(self) -> Dict[str, bool]:
        """重启所有服务"""
        results = {}
        for name in self.SERVICES:
            results[name] = self.restart_service(name)
        return results
    
    # ========== 内存监控 ==========
    
    def get_memory_usage(self, service_name: str) -> Optional[int]:
        """
        获取服务内存使用
        
        Args:
            service_name: 服务名称
            
        Returns:
            内存使用量(字节), None如果获取失败
        """
        service = self.SERVICES.get(service_name)
        if not service:
            return None
            
        process_name = service["process_name"]
        cmd = f"ps -o rss= -p $(pidof {process_name}) 2>/dev/null"
        result = self._run_shell(cmd)
        
        try:
            # 返回的是KB，转换为字节
            return int(result.strip()) * 1024
        except:
            return None
    
    def get_system_memory(self) -> Dict[str, int]:
        """
        获取系统内存信息
        
        Returns:
            {
                "total": 总内存(字节),
                "free": 可用内存(字节),
                "used": 已用内存(字节)
            }
        """
        cmd = "cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable'"
        result = self._run_shell(cmd)
        
        mem_info = {}
        for line in result.split('\n'):
            if 'MemTotal' in line:
                mem_info['total'] = int(line.split()[1]) * 1024  # KB to bytes
            elif 'MemFree' in line:
                mem_info['free'] = int(line.split()[1]) * 1024
            elif 'MemAvailable' in line:
                mem_info['available'] = int(line.split()[1]) * 1024
                
        mem_info['used'] = mem_info.get('total', 0) - mem_info.get('available', 0)
        return mem_info
    
    def cleanup_memory(self) -> bool:
        """
        清理内存
        
        Returns:
            是否成功
        """
        self._log_event("正在清理内存...")
        
        try:
            # 清理缓存
            cmd = "sync && echo 3 > /proc/sys/vm/drop_caches"
            self._run_shell(cmd)
            
            # 杀掉不重要的后台进程
            cmd = "pm trim-caches 100M"
            self._run_shell(cmd)
            
            # 检查清理后内存
            mem = self.get_system_memory()
            self._log_event(f"内存清理完成，可用: {mem.get('available', 0) / 1024 / 1024:.1f}MB")
            return True
        except Exception as e:
            self._log_event(f"内存清理失败: {e}")
            return False
    
    # ========== 自动监控 ==========
    
    def start_monitoring(self, 
                         on_status_change: Optional[Callable] = None,
                         on_error: Optional[Callable] = None):
        """
        开始监控
        
        Args:
            on_status_change: 状态变化回调(status_dict)
            on_error: 错误回调(error_msg)
        """
        if self._running:
            return
            
        self._running = True
        if on_status_change:
            self._callbacks.append(on_status_change)
            
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self._log_event("✓ 服务监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self._log_event("✗ 服务监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 检查所有服务状态
                status_dict = self.get_all_services_status()
                
                # 检查系统内存
                mem = self.get_system_memory()
                available_mb = mem.get('available', 0) / 1024 / 1024
                
                # 记录状态
                for name, status in status_dict.items():
                    prev_status = self._service_status.get(name)
                    self._service_status[name] = status
                    
                    # 状态变化检测
                    if prev_status and prev_status != status:
                        self._log_event(f"服务状态变化: {name} {prev_status.value} -> {status.value}")
                    
                    # 处理无响应
                    if status == ServiceStatus.UNRESPONSIVE:
                        self._unresponsive_count[name] = self._unresponsive_count.get(name, 0) + 1
                        
                        # 超过阈值，重启服务
                        if self._unresponsive_count[name] >= self.unresponsive_threshold:
                            self._log_event(f"检测到服务无响应: {name}，正在重启...")
                            self.restart_service(name)
                            self._unresponsive_count[name] = 0
                    else:
                        self._unresponsive_count[name] = 0
                
                # 内存不足时清理
                if available_mb < 100:  # 可用小于100MB
                    self._log_event(f"系统内存不足: {available_mb:.1f}MB，尝试清理...")
                    self.cleanup_memory()
                
                # 回调
                for callback in self._callbacks:
                    try:
                        callback({
                            "services": {k: v.value for k, v in status_dict.items()},
                            "memory": mem,
                            "timestamp": datetime.now().isoformat()
                        })
                    except:
                        pass
                        
            except Exception as e:
                self._log_event(f"监控循环出错: {e}")
            
            # 等待下次检查
            time.sleep(self.check_interval)
    
    # ========== 日志 ==========
    
    def _log_event(self, message: str):
        """记录事件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self._log.append(log_entry)
        
        # 保留最近100条日志
        if len(self._log) > 100:
            self._log = self._log[-100:]
    
    def get_logs(self, last_n: int = 20) -> list:
        """获取日志"""
        return self._log[-last_n:]
    
    def get_status(self) -> Dict[str, Any]:
        """获取完整状态"""
        return {
            "monitoring": self._running,
            "services": {k: v.value for k, v in self.get_all_services_status().items()},
            "memory": self.get_system_memory(),
            "last_check": datetime.now().isoformat()
        }


# ========== Web API 集成 ==========

def create_monitor_routes(app, monitor: R1ServiceMonitor):
    """创建监控相关的API路由"""
    
    @app.get("/api/monitor/status")
    async def get_monitor_status():
        """获取监控状态"""
        return monitor.get_status()
    
    @app.get("/api/monitor/services")
    async def get_services_status():
        """获取所有服务状态"""
        status = monitor.get_all_services_status()
        return {k: v.value for k, v in status.items()}
    
    @app.post("/api/monitor/restart/{service_name}")
    async def restart_service(service_name: str):
        """重启指定服务"""
        success = monitor.restart_service(service_name)
        return {"success": success, "service": service_name}
    
    @app.post("/api/monitor/restart_all")
    async def restart_all():
        """重启所有服务"""
        results = monitor.restart_all_services()
        return {"results": results}
    
    @app.get("/api/monitor/memory")
    async def get_memory():
        """获取内存信息"""
        return monitor.get_system_memory()
    
    @app.post("/api/monitor/cleanup_memory")
    async def cleanup_memory():
        """清理内存"""
        success = monitor.cleanup_memory()
        return {"success": success}
    
    @app.get("/api/monitor/logs")
    async def get_logs(last_n: int = 20):
        """获取监控日志"""
        return {"logs": monitor.get_logs(last_n)}
    
    @app.post("/api/monitor/start")
    async def start_monitor():
        """启动监控"""
        monitor.start_monitoring()
        return {"success": True}
    
    @app.post("/api/monitor/stop")
    async def stop_monitor():
        """停止监控"""
        monitor.stop_monitoring()
        return {"success": True}
