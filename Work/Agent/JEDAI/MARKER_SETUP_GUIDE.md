# marker-pdf 系统级安装指南

## 📦 安装方法

### 方法 1：自动安装（推荐）

在 PowerShell 中运行：

```powershell
cd C:\Users\wentao\Desktop\AAI\Main_work\ACL\JEDAI
.\install_marker.ps1
```

### 方法 2：手动安装

```powershell
# 1. 安装包
pip install marker-pdf --upgrade

# 2. 查找安装位置
python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))"
# 或者
python -c "import site; print(site.USER_BASE + '\\Scripts')"

# 3. 将上述路径添加到系统PATH
# Windows设置 > 系统 > 关于 > 高级系统设置 > 环境变量
# 编辑用户变量 Path，添加上述Scripts路径

# 4. 重启终端
```

---

## 🚀 使用方法

### 基本命令

```powershell
# 转换单个PDF
marker_single "input.pdf" "output.md"

# 使用便捷命令（安装后可用）
pdf2md "input.pdf"  # 自动命名为 input.md
pdf2md "input.pdf" "output.md"  # 指定输出名称
```

### 转换 JedAI Integration PDF

```powershell
# 进入目录
cd C:\Users\wentao\Desktop\AAI\Main_work\ACL\JEDAI

# 转换PDF
marker_single "JedAI Integration with LangChain.pdf" "JedAI_Integration_with_LangChain.md"

# 或使用便捷命令
pdf2md "JedAI Integration with LangChain.pdf"
```

---

## ⚙️ 高级选项

```powershell
# 使用更多线程加速（推荐）
marker_single input.pdf output.md --batch_multiplier 4

# 保留图片到单独文件夹
marker_single input.pdf output.md --output_format markdown --extract_images

# 仅转换特定页面
marker_single input.pdf output.md --pages 1-10
```

---

## 🐛 故障排除

### 问题1：找不到 marker_single 命令

**解决方案A：使用Python模块方式**
```powershell
python -m marker.convert_single "input.pdf" "output.md"
```

**解决方案B：创建别名脚本**

创建文件 `pdf2md.bat` 并放在任意PATH目录下：
```batch
@echo off
python -m marker.convert_single %*
```

### 问题2：缺少依赖

```powershell
# 安装OCR支持（可选）
pip install pytesseract tesseract

# 安装GPU加速（可选，需要CUDA）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 问题3：转换速度慢

```powershell
# 使用多线程
marker_single input.pdf output.md --batch_multiplier 4 --max_pages 500

# 或关闭某些功能加速
marker_single input.pdf output.md --disable_image_extraction
```

---

## 📝 Python 脚本使用

如果命令行方式有问题，可以使用Python脚本：

```python
# convert_pdf.py
from marker.convert import convert_single_pdf
from pathlib import Path

def convert_pdf_to_md(pdf_path: str, output_path: str = None):
    """转换PDF为Markdown"""
    pdf_file = Path(pdf_path)
    
    if output_path is None:
        output_path = pdf_file.with_suffix('.md')
    
    print(f"Converting: {pdf_path} -> {output_path}")
    
    # 转换
    result = convert_single_pdf(
        pdf_path,
        output_path,
        batch_multiplier=2
    )
    
    print(f"✓ Conversion complete: {output_path}")
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python convert_pdf.py input.pdf [output.md]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_pdf_to_md(pdf_path, output_path)
```

使用方法：
```powershell
python convert_pdf.py "JedAI Integration with LangChain.pdf"
```

---

## 🎯 快速转换当前PDF

```powershell
# 方案1：直接使用marker（如果已安装）
marker_single "JedAI Integration with LangChain.pdf" "JedAI_LangChain.md"

# 方案2：使用Python模块
python -m marker.convert_single "JedAI Integration with LangChain.pdf" "JedAI_LangChain.md"

# 方案3：使用在线转换器
# https://www.ilovepdf.com/pdf_to_word (然后复制内容)
# https://pdf2md.morethan.io/
```

---

## 💡 替代方案

如果 marker-pdf 安装困难，可以使用：

### 1. PyMuPDF4LLM（更轻量）
```powershell
pip install pymupdf4llm
python -c "import pymupdf4llm; print(pymupdf4llm.to_markdown('input.pdf'))" > output.md
```

### 2. PyPDF2（基础版）
```powershell
pip install pypdf2
```

```python
from pypdf2 import PdfReader

reader = PdfReader("input.pdf")
text = "\n\n".join([page.extract_text() for page in reader.pages])

with open("output.md", "w", encoding="utf-8") as f:
    f.write(text)
```

### 3. 使用多模态AI（最推荐）
- 直接上传PDF到Claude/GPT-4o
- 要求输出为Markdown格式
- AI能理解图片和表格内容

---

## 📚 参考资源

- marker-pdf GitHub: https://github.com/VikParuchuri/marker
- 文档: https://github.com/VikParuchuri/marker/blob/main/README.md
- PyMuPDF4LLM: https://pymupdf.readthedocs.io/
