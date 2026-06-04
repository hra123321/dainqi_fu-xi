# 电气复习助手 - Android App 构建指南

## 环境要求
- Flutter SDK >= 3.0.0
- Android SDK (API 31+, Android 12+)
- Java 17+

## 构建步骤

### 1. 安装 Flutter SDK
访问 https://docs.flutter.dev/get-started/install/windows
下载并安装 Flutter SDK

### 2. 配置环境变量
flutter config --android-sdk <你的Android SDK路径>

### 3. 构建 APK
cd android_app
flutter pub get
flutter build apk --release

### 4. 安装到手机
- 生成的 APK 在: android_app/build/app/outputs/flutter-apk/app-release.apk
- 传到手机安装即可

## 连接模式说明

### WiFi 连接（推荐）
1. 电脑启动后端: cd 项目根目录 && python main.py
2. 手机连同一个校园网 WiFi
3. App 中输入电脑的 IP 地址
4. 电脑 IP 查看: ipconfig (Windows)

### USB 有线连接
1. 手机开启 USB 网络共享（设置 > 连接 > USB网络共享）
2. 电脑 IP 变为 192.168.42.x
3. App 中输入该 IP

### 手机本地处理
- 需要安装完整 App 版本
- OCR 和 AI 处理在手机本地进行
- 需在 App 中配置 DeepSeek API Key

## 开发环境
- 如果使用 Android Studio 开发:
  File > Open > 选择 android_app 目录
  等待 Gradle 同步完成后即可运行
