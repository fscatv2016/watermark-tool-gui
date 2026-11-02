# 图片水印工具

基于 **Tkinter + Pillow** 的桌面图片水印程序：文字/图片水印、透明度、平铺、批量导出。

## 运行（开发）

```bash
pip install -r requirements.txt
python watermark_tool.py
```

## Windows 双击运行

见 [README_WINDOWS.md](README_WINDOWS.md)。在 Windows 上双击 `build_windows.bat` 即可生成 `dist\图片水印工具.exe`。

## 主要文件

| 文件 | 说明 |
|------|------|
| `watermark_tool.py` | 主程序 |
| `watermark.spec` | PyInstaller 配置 |
| `build_windows.bat` | Windows 一键打包 |
| `fonts/` | 内置中文字体（Noto Sans SC） |
