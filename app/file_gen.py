import os
from fpdf import FPDF
from docx import Document

def generate_pdf(content: str, filename: str = "output.pdf") -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Handle multi-line content
    for line in content.split('\n'):
        # using multi_cell to handle line wrapping
        pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))
    
    filepath = os.path.join(os.getcwd(), filename)
    pdf.output(filepath)
    return filepath

def generate_docx(content: str, filename: str = "output.docx") -> str:
    doc = Document()
    doc.add_paragraph(content)
    filepath = os.path.join(os.getcwd(), filename)
    doc.save(filepath)
    return filepath
