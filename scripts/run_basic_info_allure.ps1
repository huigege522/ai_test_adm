# -*- coding: utf-8 -*-
# 基本信息管理 API 测试 + 清空并生成 Allure 报告
# 用法（在项目根 ai_test_adm 下）:
#   powershell -ExecutionPolicy Bypass -File scripts/run_basic_info_allure.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/run_basic_info_allure.ps1 -Serve

param(
    [switch]$Serve  # 加 -Serve 则在跑完后 allure serve（临时服务）；默认 allure open 静态报告
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Results = "reports/allure-results"
$Report = "reports/allure-report"

if (Test-Path $Results) { Remove-Item -Recurse -Force $Results }
if (Test-Path $Report) { Remove-Item -Recurse -Force $Report }
New-Item -ItemType Directory -Force -Path $Results | Out-Null

$TestFiles = @("tests/api/basic_info/")

Write-Host ">> pytest (Allure 结果目录: $Results)" -ForegroundColor Cyan
python -m pytest @TestFiles -v --alluredir=$Results
$PytestExit = $LASTEXITCODE

Write-Host ">> allure generate --clean" -ForegroundColor Cyan
allure generate $Results -o $Report --clean

if ($Serve) {
    Write-Host ">> allure serve (Ctrl+C 结束)" -ForegroundColor Cyan
    allure serve $Results
} else {
    Write-Host ">> allure open $Report" -ForegroundColor Cyan
    allure open $Report
}

exit $PytestExit
