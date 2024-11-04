from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

def clean_pdf(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Footer content with only the registered address line, without toll-free
    footer_line = "Regd.&Corporate Office: 1, New Tank Street, Valluvar Kottam High Road, Nungambakkam, Chennai - 600034, Phone: 044 -28302700 / 28288800"
    footer_y_position = 0.5 * inch  # Position at the bottom of the page

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()

        if text and text.strip():
            # Create an in-memory canvas to add footer content without duplicating
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Draw only the registered address line at the desired position
            can.drawString(72, footer_y_position, footer_line)  # Adjust x-position if needed for alignment

            can.save()
            packet.seek(0)

            # Overlay the footer onto the existing page content
            footer_pdf = PdfReader(packet)
            page.merge_page(footer_pdf.pages[0])
            writer.add_page(page)

    # Write the final output PDF with the aligned footer
    with open(output_path, "wb") as final_pdf:
        writer.write(final_pdf)

if __name__ == "__main__":
    clean_pdf("input/KISHORE_MEDICAL_INSURANCE_BILL_2024_FINAL.pdf", "output/output.pdf")
