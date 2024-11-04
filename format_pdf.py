from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

def clean_pdf(input_path, output_path):
    # Step 1: Read original PDF and remove unwanted pages
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()
        if text and text.strip():
            # Process each page with reportlab for formatting
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Draw alignment content on each page
            can.drawString(1 * inch, 0.5 * inch, "Aligned footer content here")  # Footer example
            can.save()

            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            new_pdf = PdfReader(packet)

            # Merge the original page content with the footer
            page.merge_page(new_pdf.pages[0])
            writer.add_page(page)

    # Write final output PDF
    with open(output_path, "wb") as final_pdf:
        writer.write(final_pdf)

if __name__ == "__main__":
    clean_pdf("input/KISHORE_MEDICAL_INSURANCE_BILL_2024_FINAL.pdf", "output/output.pdf")
