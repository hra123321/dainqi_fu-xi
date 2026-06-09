"""
============================================
 图片处理服务 — 拍照题目的 OCR 识别
============================================
【作用】
接收手机拍摄的题目照片，提取文字内容。
支持多种 OCR 引擎，自动检测可用引擎。
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict
from PIL import Image

from app.utils.logger import logger


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ImageProcessor:
    """
    【图片处理器】
    
    接收图片 → 保存 → OCR 识别 → 返回文字。
    """

    def __init__(self):
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """检查 Tesseract OCR 是否已安装"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def save_upload(self, image_data: bytes, filename: str = "photo.jpg") -> str:
        """保存上传的图片到本地"""
        ext = os.path.splitext(filename)[1] or ".jpg"
        saved_name = f"{uuid.uuid4().hex}{ext}"
        saved_path = UPLOAD_DIR / saved_name
        with open(saved_path, "wb") as f:
            f.write(image_data)
        logger.info(f"[图片] 已保存: {saved_name} ({len(image_data)} bytes)")
        return str(saved_path)

    def extract_text(self, image_path: str) -> Dict:
        """
        【OCR 文字识别】
        
        从图片中提取文字。
        如果有 Tesseract 就用它，否则返回提示。
        """
        if not os.path.isfile(image_path):
            return {"success": False, "error": "文件不存在"}

        if self._tesseract_available:
            try:
                import pytesseract
                img = Image.open(image_path)
                # 中文识别
                text = pytesseract.image_to_string(img, lang="chi_sim+eng")
                text = text.strip()
                if text:
                    return {"success": True, "text": text, "engine": "tesseract"}
                else:
                    return {"success": False, "text": "", "error": "未识别到文字"}
            except Exception as e:
                return {"success": False, "error": f"OCR 失败: {str(e)}"}
        else:
            return {
                "success": False,
                "text": "",
                "error": "未安装 OCR 引擎。请安装 Tesseract-OCR:\n"
                         "1. 下载: https://github.com/UB-Mannheim/tesseract/wiki\n"
                         "2. 安装时勾选中文语言包\n"
                         "3. 或使用手机本地处理模式",
            }

    def cleanup(self, image_path: str):
        """清理临时图片"""
        try:
            if os.path.isfile(image_path):
                os.remove(image_path)
        except Exception:
            pass


# ==================== 获取本机网络信息 ====================
import socket

def get_network_info() -> Dict:
    """
    【获取本机网络信息】
    
    返回本机在校园网/局域网中的 IP 地址，
    供手机端连接时使用。
    
    校园网环境说明:
    电脑通常有两个 IP：
    - 127.0.0.1（本机回环）
    - 192.168.x.x 或 10.x.x.x（校园网分配的地址）
    """
    hostname = socket.gethostname()
    ips = []
    
    # 获取所有网络接口的 IP
    try:
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip != "127.0.0.1" and not ip.startswith("::"):
                ips.append(ip)
        ips = list(set(ips))
    except Exception:
        ips = ["无法获取"]
    
    return {
        "hostname": hostname,
        "ip_addresses": ips,
        "suggested_url": f"http://{ips[0] if ips else 'localhost'}:8000",
        "port": 8000,
        "note": "校园网环境下，手机和电脑需连接同一个校园网 WiFi",
    }


# ==================== 全局实例 ====================
image_processor = ImageProcessor()
