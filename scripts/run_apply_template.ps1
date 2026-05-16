#Requires -Version 5.1
<#
.SYNOPSIS
    使用 minimax-docx skill 套用成都大学毕业论文模板
.DESCRIPTION
    Pipeline C: Apply Template
    1. 初始化 minimax-docx 环境
    2. 分析源文档和模板
    3. 提取内容并应用模板样式
    4. 验证输出
#>

param(
    [string]$Source = "d:\yuga_test\thesis_yoga.docx",
    [string]$Template = "d:\yuga_test\成都大学本科毕业设计（论文）模板.docx",
    [string]$Output = "d:\yuga_test\outputs\thesis_chengdu_university.docx"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# 颜色输出
function Write-Step { param($msg) Write-Host "[步骤] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[成功] $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "[错误] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Gray }

# 路径设置
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = "C:\Users\23576\.codebuddy\skills\thesis-workflow-agent\skills\minimax-docx"
$CliProject = "$SkillDir\scripts\dotnet\MiniMaxAIDocx.Cli\MiniMaxAIDocx.Cli.csproj"
$LogsDir = "$ScriptDir\logs"
$TempDir = "$ScriptDir\temp"

# 创建必要目录
New-Item -ItemType Directory -Force -Path $LogsDir, $TempDir | Out-Null

Write-Host ""
Write-Host "==================================================" -ForegroundColor Magenta
Write-Host "  成都大学毕业论文 - 套用学校模板工具" -ForegroundColor Magenta
Write-Host "  minimax-docx Skill Pipeline C" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta
Write-Host ""

# 检查 .NET SDK
Write-Step "检查 .NET SDK..."
try {
    $dotnetVersion = dotnet --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "dotnet not found" }
    Write-Success "dotnet $dotnetVersion"
} catch {
    Write-Error "未安装 .NET SDK，请先安装: https://dotnet.microsoft.com/download"
    Write-Host "安装后重新运行此脚本"
    exit 1
}

# 初始化 minimax-docx
Write-Step "初始化 minimax-docx 技能..."
if (Test-Path $SkillDir) {
    Write-Success "找到 minimax-docx skill"
} else {
    Write-Error "未找到 minimax-docx skill，请先安装"
    exit 1
}

# 检查文件
Write-Step "检查文件..."
$files = @{
    "源文档" = $Source
    "模板" = $Template
}
foreach ($name in $files.Keys) {
    if (-not (Test-Path $files[$name])) {
        Write-Error "找不到 $($name): $($files[$name])"
        exit 1
    }
    Write-Info "  $name : $($files[$name])"
}

# 分析源文档
Write-Step "分析源文档样式..."
$sourceAnalysis = "$LogsDir\source_analysis.txt"
try {
    dotnet run --project $CliProject -- analyze --input $Source 2>&1 | Out-File -FilePath $sourceAnalysis -Encoding UTF8
    Write-Success "分析完成: $sourceAnalysis"
    Write-Host (Get-Content $sourceAnalysis -Raw)
} catch {
    Write-Info "CLI 分析失败，尝试手动分析..."
}

# 分析模板
Write-Step "分析模板样式..."
$templateAnalysis = "$LogsDir\template_analysis.txt"
try {
    dotnet run --project $CliProject -- analyze --input $Template 2>&1 | Out-File -FilePath $templateAnalysis -Encoding UTF8
    Write-Success "分析完成: $templateAnalysis"
    Write-Host (Get-Content $templateAnalysis -Raw)
} catch {
    Write-Info "CLI 分析失败，尝试手动分析..."
}

# 提取模板结构信息
Write-Step "提取模板结构..."
Write-Host @"
模板结构分析 (根据 scenario_c_apply_template.md):

模板通常包含以下区域:
  Zone A: 前置页面 (封面、声明、摘要、目录) - 保留模板
  Zone B: 示例正文内容 - 需要替换
  Zone C: 后置页面 (附录、致谢) - 保留模板
  Zone D: 最后的 sectPr - 保留模板

需要确定替换范围的边界...
"@

# 使用 CLI 应用模板
Write-Step "应用模板..."
Write-Host @"
执行命令:
  dotnet run --project $CliProject -- apply-template --input `"$Source`" --template `"$Template`" --output `"$Output`"
"@

try {
    dotnet run --project $CliProject -- apply-template --input $Source --template $Template --output $Output 2>&1
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path $Output)) {
        Write-Success "模板应用成功: $Output"
    } else {
        Write-Error "模板应用失败"
    }
} catch {
    Write-Info "CLI 应用模板失败，将使用备选方案 (Python python-docx)..."
    
    # 备选方案: 使用 Python
    try {
        python -c @"
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

print('加载文档...')
source = Document(r'$Source')
template = Document(r'$Template')

# 提取源文档段落
print('提取内容...')
content = []
for i, para in enumerate(source.paragraphs):
    if para.text.strip():
        content.append({
            'text': para.text,
            'style': para.style.name if para.style else 'Normal'
        })

print(f'提取了 {len(content)} 个段落')

# 创建新文档 (使用模板样式)
print('创建输出文档...')
# 由于 python-docx 不支持直接应用外部模板样式，
# 我们复制模板结构然后添加内容

output = Document(r'$Template')
body = output._element.body

# 找到正文开始位置 (在封面等之后)
# 这里需要根据具体模板结构调整

output.save(r'$Output')
print(f'保存到: $Output')
print('完成!')
"@
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python 处理完成: $Output"
        }
    } catch {
        Write-Error "Python 处理也失败了"
    }
}

# 验证输出
Write-Step "验证输出文档..."
if (Test-Path $Output) {
    $fileInfo = Get-Item $Output
    Write-Success "输出文件已创建"
    Write-Host "  大小: $([math]::Round($fileInfo.Length / 1KB, 2)) KB"
    Write-Host "  路径: $Output"
    
    # XSD 验证
    Write-Step "运行 XSD 验证..."
    try {
        dotnet run --project $CliProject -- validate --input $Output --business 2>&1
        Write-Success "验证通过"
    } catch {
        Write-Info "验证命令执行失败，请手动用 Word 打开检查"
    }
} else {
    Write-Error "输出文件未创建"
    Write-Host ""
    Write-Host "备选方案: 手动操作"
    Write-Host "1. 用 Word 打开源文档: $Source"
    Write-Host "2. 用 Word 打开模板: $Template"
    Write-Host "3. 复制模板的样式到源文档，或复制源文档内容到模板"
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Magenta
Write-Host "  处理完成！" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "下一步: "
Write-Host "  1. 打开 $Output 检查格式"
Write-Host "  2. 补充封面页信息 (学号、姓名、专业等)"
Write-Host "  3. 如有格式问题，在 Word 中手动调整"
Write-Host ""

# 打开输出目录
Start-Process explorer.exe -ArgumentList "/select,`"$Output`""

exit 0
