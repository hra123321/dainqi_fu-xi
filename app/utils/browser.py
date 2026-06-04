"""
============================================
 Edge 浏览器启动器
============================================
【作用】
项目启动时自动调用 Edge 浏览器打开前端页面。
强制使用 Edge，禁止使用 Chrome/Firefox 等（硬性约束）。

【为什么不用 webbrowser.open()？】
Python 自带的 webbrowser.open() 会打开"系统默认浏览器"，
而用户可能默认是 Chrome。所以我们要手动指定 Edge 路径。

【原理】
subprocess.Popen() 可以在 Windows 中启动一个新程序。
它不会阻塞当前 Python 程序（程序继续运行）。
"""

import subprocess
import os
import webbrowser
from typing import Optional

from app.config import settings


def open_edge(url: str = "http://127.0.0.1:8000") -> Optional[bool]:
    """
    【在 Edge 中打开指定网址】
    
    参数:
        url: 要打开的网址，默认是本机地址 8000 端口
    
    返回:
        True  = 成功打开
        False = 打开失败（Edge 没找到）
    
    异常:
        不抛出异常，失败只返回 False
    """
    # 从配置文件读取 Edge 浏览器路径
    edge_path = settings.EDGE_PATH
    
    # 检查 Edge 可执行文件是否存在
    if not os.path.isfile(edge_path):
        # Edge 没找到，给出清晰的安装提示
        print(f"[Edge启动器] Edge 浏览器未找到: {edge_path}")
        print("[Edge启动器] 请确认 Edge 已安装，或修改 config.py 中的 EDGE_PATH")
        return False
    
    try:
        # 启动 Edge 进程
        # subprocess.Popen 的参数说明：
        #   [edge_path, url]  = 相当于在命令行输入: msedge.exe http://...
        #   shell=True        = 通过系统 Shell 启动
        subprocess.Popen(
            [edge_path, url],
            shell=True,
        )
        print(f"[Edge启动器] 已在 Edge 中打开: {url}")
        return True
    
    except Exception as e:
        print(f"[Edge启动器] 打开失败: {e}")
        return False


def open_edge_fallback(url: str = "http://127.0.0.1:8000") -> bool:
    """
    【备用启动方式：尝试通过系统命令启动 Edge】
    
    如果主方法失败，尝试通过 start 命令（Windows）启动。
    """
    try:
        # Windows 的 start msedge 命令会自动找 Edge
        subprocess.Popen(
            f'start msedge "{url}"',
            shell=True,
        )
        return True
    except Exception as e:
        print(f"[Edge启动器] 备用方式也失败了: {e}")
        return False


def try_open_browser(url: str = "http://127.0.0.1:8000"):
    """
    【统一入口：尝试用 Edge 打开，失败则用 fallback】
    
    先尝试直接调用 Edge 可执行文件，
    如果失败（Edge 路径不对），尝试 Windows start 命令。
    最后还是失败的话，给出手动打开的提示。
    """
    print(f"\n[Edge启动器] 正在尝试打开: {url}")
    
    success = open_edge(url)
    
    if not success:
        print("[Edge启动器] 尝试备用方式...")
        success = open_edge_fallback(url)
    
    if not success:
        print(f"[Edge启动器] 所有自动打开方式都失败了，请手动在 Edge 中打开:\n  {url}")
