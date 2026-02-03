#!/usr/bin/env python3
"""
Read PDF content and extract text using pymupdf4llm
"""
import sys
import subprocess

# Install pymupdf4llm if not available
try:
    import pymupdf4llm
except ImportError:
    print("Installing pymupdf4llm...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf4llm"])
    import pymupdf4llm

def read_pdf_pymupdf4llm(pdf_path):
    """Read PDF using pymupdf4llm - optimized for LLM processing"""
    # pymupdf4llm returns markdown formatted text
    md_text = pymupdf4llm.to_markdown(pdf_path)
    return md_text

if __name__ == "__main__":
    pdf_path = r"c:\Users\wentao\Desktop\AAI\Main_work\ACL\JEDAI\JedAI Agent Tooling & Function Calling.pdf"
    
    print("Using pymupdf4llm to read PDF...")
    
    try:
        content = read_pdf_pymupdf4llm(pdf_path)
        
        # Save to markdown file
        output_path = pdf_path.replace('.pdf', '.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ PDF content extracted to: {output_path}")
        print(f"✓ Total characters: {len(content)}")
        print(f"\n{'='*80}")
        print("Preview (first 3000 characters):")
        print(f"{'='*80}\n")
        print(f"{content[:3000]}...")
        
    except Exception as e:
        print(f"Error reading PDF: {e}")
        import traceback
        traceback.print_exc()
