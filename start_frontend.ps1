# CodeReview AI 前端启动脚本
Write-Host "🚀 启动 CodeReview AI 前端..." -ForegroundColor Green
Write-Host "=========================================="

# 检查Node.js
Write-Host "[1/3] 检查Node.js环境..." -ForegroundColor Yellow
$nodeVersion = node --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 未找到Node.js，请先安装Node.js" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Node.js版本: $nodeVersion" -ForegroundColor Green

# 进入前端目录
Set-Location "D:\CodeReviewAI\frontend"

# 检查依赖
Write-Host "[2/3] 检查依赖..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 安装依赖..." -ForegroundColor Cyan
    npm install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ 依赖已安装" -ForegroundColor Green

# 启动开发服务器
Write-Host "[3/3] 启动开发服务器..." -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📊 服务器信息：" -ForegroundColor Cyan
Write-Host "   前端：http://localhost:3000" -ForegroundColor White
Write-Host "   后端：http://localhost:8000" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 正在启动开发服务器..." -ForegroundColor Green
Write-Host "   按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 启动React开发服务器
npm start