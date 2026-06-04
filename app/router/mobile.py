"""
============================================
 移动端专用路由 — 拍照上传、网络发现
============================================
"""

import os
from fastapi import APIRouter, UploadFile, File, Form
from app.services.image_service import image_processor, get_network_info
from app.utils.logger import logger

router = APIRouter(prefix="/api/mobile", tags=["移动端"])


@router.post("/photo/upload")
async def upload_photo(file: UploadFile = File(...)):
    """
    【拍照上传】
    
    手机拍照上传题目图片，后端 OCR 识别后返回文字。
    """
    content = await file.read()
    
    # 检查文件大小（限制 20MB）
    if len(content) > 20 * 1024 * 1024:
        return {"success": False, "error": "图片过大，请压缩后重试（限制20MB）"}
    
    # 保存图片
    saved_path = image_processor.save_upload(content, file.filename or "photo.jpg")
    
    # OCR 识别
    result = image_processor.extract_text(saved_path)
    
    # 清理临时文件
    image_processor.cleanup(saved_path)
    
    if result["success"]:
        return {
            "success": True,
            "text": result["text"],
            "engine": result.get("engine", "unknown"),
            "chars": len(result["text"]),
        }
    else:
        # OCR 失败但仍然返回图片已保存的信息
        return {
            "success": True,
            "text": result.get("text", ""),
            "ocr_error": result.get("error", ""),
            "note": "文字识别失败，可手动输入题目",
        }


@router.get("/network-info")
async def network_info():
    """
    【网络发现】
    
    手机端通过这个接口获取电脑的网络信息，
    自动配置连接地址。
    """
    return get_network_info()


@router.get("/config")
async def mobile_config():
    """
    【移动端配置】
    
    返回手机 App 需要的配置信息。
    包括：API 地址、功能开关等。
    """
    from app.config import settings
    
    return {
        "app_name": "电气复习助手",
        "version": "1.0.0",
        "api_version": "v1",
        "features": {
            "photo_upload": True,
            "ocr": True,
            "qa": True,
        },
        "connection_modes": [
            {
                "id": "network",
                "name": "WiFi 连接（校园网）",
                "description": "手机通过校园网 WiFi 连接电脑服务器",
                "requires_server": True,
                "setup_steps": [
                    "1. 确保手机和电脑连接同一个校园网 WiFi",
                    "2. 电脑启动本系统 (python main.py)",
                    "3. 手机打开 App，自动发现或手动输入电脑 IP",
                ],
            },
            {
                "id": "usb",
                "name": "USB 有线连接",
                "description": "手机通过 USB 线连接电脑",
                "requires_server": True,
                "setup_steps": [
                    "1. 用 USB 数据线连接手机和电脑",
                    "2. 手机打开 USB 网络共享",
                    "3. 电脑启动本系统 (python main.py)",
                    "4. 手机通过 192.168.42.x 访问电脑",
                ],
            },
            {
                "id": "local",
                "name": "手机本地处理",
                "description": "所有处理在手机本地完成（需安装完整 App）",
                "requires_server": False,
                "setup_steps": [
                    "1. 安装 App 到手机",
                    "2. 拍照或选择题目图片",
                    "3. 手机本地 OCR 识别",
                    "4. 调用 DeepSeek API（需手机配置 Key）",
                ],
            },
        ],
    }
