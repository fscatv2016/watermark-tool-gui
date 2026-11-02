# 图片水印工具 — Windows 双击运行打包说明

本工具是 Tkinter + Pillow 的桌面 GUI。可在 **Windows** 上打成单个 `.exe`，双击即可使用。

> 当前开发机是 macOS，**无法直接交叉编译出 Windows exe**。请把整个 `watermark` 文件夹拷到 Windows 电脑后执行下面的一键脚本。

## 一键打包（推荐）

1. 安装 [Python 3.10+](https://www.python.org/downloads/windows/)（安装时勾选 **Add python.exe to PATH**）
2. 将整个项目目录拷到 Windows（需包含）：
   - `watermark_tool.py`
   - `watermark.spec`
   - `build_windows.bat`
   - `fonts\NotoSansSC-Regular.ttf`（内置中文字体，保证英文系统也能出中文水印）
   - `requirements.txt`
3. 双击 **`build_windows.bat`**（或在该目录打开 PowerShell 运行 `.\build_windows.ps1`）
4. 等待结束后，可执行文件在：

```text
dist\图片水印工具.exe
```

5. **双击** `图片水印工具.exe` 即可打开界面（无黑色控制台窗口）。

可将该 exe 单独拷贝给他人使用；首次启动可能稍慢（单文件解压）。杀毒软件偶发误报时，添加信任即可。

## 手动命令（等价）

```bat
python -m pip install "Pillow>=10.0" "pyinstaller>=6.0"
python -m PyInstaller --noconfirm watermark.spec
```

## 打包配置要点（`watermark.spec`）

| 项 | 说明 |
|----|------|
| `console=False` | GUI 程序，不弹出黑框 |
| one-file `EXE(...)` | 单文件 exe，便于分发 |
| `datas=[("fonts","fonts")]` | 打入内置中文字体 |
| Pillow / tkinter | 已列入 hiddenimports |

## 源码直接运行（开发调试）

```bat
python -m pip install -r requirements.txt
python watermark_tool.py
```

Windows 上界面字体优先用「微软雅黑」；水印文字优先用内置 Noto Sans SC，找不到再回退系统字体（微软雅黑 / 黑体等）。

## 目录结构

```text
watermark/
  watermark_tool.py      # 主程序
  watermark.spec         # PyInstaller 配置
  build_windows.bat      # 一键打包（CMD）
  build_windows.ps1      # 一键打包（PowerShell）
  fonts/
    NotoSansSC-Regular.ttf
  requirements.txt
  README_WINDOWS.md      # 本说明
  dist/                  # 打包后生成
    图片水印工具.exe
```
