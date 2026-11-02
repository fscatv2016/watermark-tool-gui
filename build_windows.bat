@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo  图片水印工具 - Windows 打包脚本
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 python。请先安装 Python 3.10+ 并勾选 "Add to PATH"。
  echo 下载: https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

echo [1/4] 安装依赖 Pillow + PyInstaller ...
python -m pip install --upgrade pip
python -m pip install "Pillow>=10.0" "pyinstaller>=6.0"
if errorlevel 1 (
  echo [错误] 依赖安装失败
  pause
  exit /b 1
)

echo.
echo [2/4] 清理旧的构建产物 ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] 使用 PyInstaller 打包（无控制台 GUI 单文件）...
python -m PyInstaller --noconfirm watermark.spec
if errorlevel 1 (
  echo [错误] 打包失败
  pause
  exit /b 1
)

echo.
echo [4/4] 完成
echo ----------------------------------------
echo 可执行文件位置:
echo   %cd%\dist\图片水印工具.exe
echo.
echo 使用方法: 双击 dist\图片水印工具.exe 即可打开图形界面。
echo 无需安装 Python；可拷贝到其他 Windows 电脑直接运行。
echo ----------------------------------------
explorer dist
pause
