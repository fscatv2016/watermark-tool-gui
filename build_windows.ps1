# 图片水印工具 - Windows 打包（PowerShell）
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
Write-Host "安装依赖..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install "Pillow>=10.0" "pyinstaller>=6.0"
Write-Host "清理旧产物..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Write-Host "PyInstaller 打包..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm watermark.spec
$exe = Join-Path $PSScriptRoot "dist\图片水印工具.exe"
if (Test-Path $exe) {
  Write-Host "成功: $exe" -ForegroundColor Green
  Write-Host "双击该 exe 即可运行（无需 Python）。"
} else {
  throw "未找到输出 exe"
}
