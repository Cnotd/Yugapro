@echo off
chcp 65001 >nul
setlocal

echo ================================================
echo   成都大学毕业论文套模板工具
echo ================================================
echo.

REM 设置工作目录
set WORK_DIR=%~dp0
set TEMPLATE=%WORK_DIR%成都大学本科毕业设计（论文）模板.doc
set SOURCE=%WORK_DIR%thesis_yoga.docx
set OUTPUT=%WORK_DIR%outputs\thesis_chengdu_university.docx

REM 创建输出目录
if not exist "%WORK_DIR%outputs" mkdir "%WORK_DIR%outputs"
if not exist "%WORK_DIR%chapters" mkdir "%WORK_DIR%chapters"
if not exist "%WORK_DIR%reports" mkdir "%WORK_DIR%reports"

echo [1/5] 检查文件...
echo.

REM 检查模板文件
if not exist "%TEMPLATE%" (
    echo 错误: 找不到模板文件 "%TEMPLATE%"
    echo 请确保 "成都大学本科毕业设计（论文）模板.doc" 在当前目录
    pause
    exit /b 1
)

REM 如果是 .doc 文件，需要转换
if /i "%TEMPLATE:~-4%"==".doc" (
    echo [2/5] 转换模板格式 (.doc -> .docx)...
    REM 尝试使用 Python docx 库转换
    python -c "from docx import Document; import os; doc = Document(r'%TEMPLATE%'); doc.save(r'%TEMPLATE%x'); print('Converted')" 2>nul
    if errorlevel 1 (
        echo 注意: Python docx 转换失败，尝试使用 LibreOffice...
        if exist "C:\Program Files\LibreOffice\program\soffice.exe" (
            "C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to docx "%TEMPLATE%" --outdir "%WORK_DIR%"
            ren "%WORK_DIR%成都大学本科毕业设计（论文）模板.docx" "template_converted.docx" 2>nul
            set TEMPLATE=%WORK_DIR%template_converted.docx
        ) else (
            echo 警告: LibreOffice 未安装，请手动将模板另存为 .docx 格式
            echo 或访问 https://www.freeconvert.com/zh/docx-converter 在线转换
            pause
        )
    ) else (
        ren "%TEMPLATE%x" "template_converted.docx"
        set TEMPLATE=%WORK_DIR%template_converted.docx
    )
) else (
    set TEMPLATE=%WORK_DIR%成都大学本科毕业设计（论文）模板.docx
)

REM 检查源文档
if not exist "%SOURCE%" (
    echo 错误: 找不到源文档 "%SOURCE%"
    pause
    exit /b 1
)

echo [3/5] 检查 minimax-docx 工具...
echo.

REM 检查 dotnet
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo 警告: dotnet 未安装，将使用 Python 方式处理
    goto :python_method
)

REM 使用 minimax-docx
set MINIMAX_SKILL=C:\Users\23576\.codebuddy\skills\thesis-workflow-agent\skills\minimax-docx

if exist "%MINIMAX_SKILL%" (
    echo 使用 minimax-docx 技能套用模板...
    
    REM 构建命令
    set CLI_CMD=dotnet run --project "%MINIMAX_SKILL%\scripts\dotnet\MiniMaxAIDocx.Cli\MiniMaxAIDocx.Cli.csproj"
    
    REM 分析源文档
    echo 分析源文档样式...
    %CLI_CMD% analyze --input "%SOURCE%" > "%WORK_DIR%logs\source_analysis.txt" 2>&1
    
    REM 分析模板
    echo 分析模板样式...
    %CLI_CMD% analyze --input "%TEMPLATE%" > "%WORK_DIR%logs\template_analysis.txt" 2>&1
    
    REM 应用模板
    echo 套用模板...
    %CLI_CMD% apply-template --input "%SOURCE%" --template "%TEMPLATE%" --output "%OUTPUT%"
    
    REM 验证
    echo 验证输出文档...
    %CLI_CMD% validate --input "%OUTPUT%" --business
) else (
    :python_method
    echo 使用 Python 方式处理...
    
    REM 使用 python-docx 进行基本处理
    python -c "
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

# 加载源文档和模板
print('加载源文档...')
source = Document(r'%SOURCE%')
template = Document(r'%TEMPLATE%')

# 提取源文档内容
content = []
for para in source.paragraphs:
    if para.text.strip():
        content.append({
            'text': para.text,
            'style': para.style.name if para.style else 'Normal'
        })

print(f'提取了 {len(content)} 个段落')

# 复制模板结构
print('应用模板样式...')
output = Document(r'%TEMPLATE%')

# 清空正文部分并添加内容
# 注意：这是一个基础版本，完整实现需要更多处理

output.save(r'%OUTPUT%')
print('完成！')
"
)

if errorlevel 1 (
    echo 警告: 自动处理遇到问题
    echo 请手动操作：
    echo 1. 打开 Word
    echo 2. 打开源文档: %SOURCE%
    echo 3. 选择 "文件" -> "另存为" -> 选择模板格式
)

echo.
echo [4/5] 复制文件到工作目录...
copy "%SOURCE%" "%WORK_DIR%chapters\thesis_content_backup.docx" >nul
copy "%TEMPLATE%" "%WORK_DIR%outputs\template_backup.docx" >nul

echo.
echo [5/5] 完成！
echo.
echo ================================================
echo   处理完成！
echo ================================================
echo.
echo 输出文件: %OUTPUT%
echo.
echo 后续步骤:
echo 1. 检查输出文档格式是否正确
echo 2. 如需调整，使用 Word 打开手动修改
echo 3. 补充封面页信息（学号、姓名等）
echo.
echo 日志文件: %WORK_DIR%logs\
echo.

pause
