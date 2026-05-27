#!/bin/bash
# News Intelligence Desktop - 安装脚本

set -e

echo "=========================================="
echo "  News Intelligence Desktop 安装脚本"
echo "=========================================="

# 检测操作系统
if [ -f /etc/debian_version ]; then
    echo "检测到 Debian/Ubuntu 系统"
    echo "安装系统依赖..."
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        libgl1-mesa-glx \
        libxkbcommon0 \
        libegl1 \
        libdbus-1-3 \
        libfontconfig1 \
        libglib2.0-0 \
        libxcb-xinerama0 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        libxcb-shm0 \
        libxcb-sync1 \
        libxcb-util1 \
        libxcb-xfixes0 \
        libxcb-xkb1
elif [ -f /etc/redhat-release ]; then
    echo "检测到 RedHat/CentOS 系统"
    echo "安装系统依赖..."
    yum install -y \
        python3 \
        python3-pip \
        mesa-libGL \
        libxkbcommon \
        mesa-libEGL \
        dbus-libs \
        fontconfig \
        glib2 \
        libxcb
else
    echo "未识别的系统，请手动安装依赖"
fi

echo ""
echo "安装 Python 依赖..."
pip3 install -r requirements.txt

echo ""
echo "安装 PySide6（图形界面）..."
pip3 install PySide6

echo ""
echo "=========================================="
echo "  安装完成！"
echo "=========================================="
echo ""
echo "启动图形界面："
echo "  python3 -m news_intelligence_desktop.app.main"
echo ""
echo "启动控制台："
echo "  python3 -m news_intelligence_desktop.app.main --console"
echo ""
