from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

def clean_pdf(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Footer content to align at the bottom of each page
    footer_lines = [
        "Regd.&Corporate Office:1,New Tank Street,Valluvar Kottam High Road,Nungambakkam,Chennai - 600034,Phone : 044 -28302700 / 28288800",
        "Toll Free No:1800-425-2255 / 1800-102-4477,CIN : L66010TN2005PLC056649 Email :support@starhealth.in Website :www.starhealth.in"
    ]

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()

        if text and text.strip():
            # Create an in-memory canvas to add footer content without altering main text
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Footer alignment position
            footer_y_position = 0.5 * inch  # Adjust for desired vertical placement

            # Draw each footer line with consistent spacing at the bottom
            for i, line in enumerate(footer_lines):
                can.drawString(72, footer_y_position + (i * 12), line)  # Adjust x-position if needed

            can.save()
            packet.seek(0)

            # Overlay footer onto the existing page content
            footer_pdf = PdfReader(packet)
            page.merge_page(footer_pdf.pages[0])
            writer.add_page(page)

    # Write the final aligned PDF
    with open(output_path, "wb") as final_pdf:
        writer.write(final_pdf)

if __name__ == "__main__":
    clean_pdf("input/KISHORE_MEDICAL_INSURANCE_BILL_2024_FINAL.pdf", "output/output.pdf")
