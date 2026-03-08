import fitz  # PyMuPDF
import sys
import os

pdf_path = sys.argv[1]
output_md = sys.argv[2]

try:
    doc = fitz.open(pdf_path)
    md_content = f"# Extracted Content from {os.path.basename(pdf_path)}\n\n"
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        md_content += f"## Page {page_num + 1}\n\n"
        md_content += text
        md_content += "\n\n---\n\n"
        
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"Extraction successful: Saved to {output_md}")
except Exception as e:
    print(f"Error extracting PDF: {e}")
