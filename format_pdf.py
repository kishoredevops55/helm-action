from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def clean_pdf(input_path, output_path):
    # Step 1: Read original PDF and remove unwanted pages
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page_num in range(len(reader.pages)):
        # Add all non-blank or specified pages to new PDF
        page = reader.pages[page_num]
        text = page.extract_text()
        if text and text.strip():
            writer.add_page(page)

    # Write interim cleaned PDF
    temp_pdf_path = "/tmp/cleaned.pdf"
    with open(temp_pdf_path, "wb") as temp_pdf:
        writer.write(temp_pdf)

    # Step 2: Align last lines and adjust formatting
    output_buffer = BytesIO()
    c = canvas.Canvas(output_buffer, pagesize=letter)
    
    # Copy and reformat each page
    temp_reader = PdfReader(temp_pdf_path)
    for page in temp_reader.pages:
        c.showPage()
        c.drawString(72, 100, "Sample aligned content")  # Example alignment for bottom
        
    c.save()
    
    with open(output_path, "wb") as final_pdf:
        final_pdf.write(output_buffer.getvalue())

if __name__ == "__main__":
    clean_pdf("input.pdf", "output.pdf")
  
