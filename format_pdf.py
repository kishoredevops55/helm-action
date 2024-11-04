from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

def clean_pdf(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Define footer content
    footer_text = "Regd.&Corporate Office: 1, New Tank Street, Valluvar Kottam High Road, Nungambakkam, Chennai - 600034, Phone: 044 -28302700 / 28288800"
    footer_y_position = 0.5 * inch  # Adjust Y-position for the bottom of the page

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()

        # Check if footer text already exists to avoid duplication
        if footer_text not in text:
            # Create a new canvas for the footer
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Draw the footer at the specified Y-position
            can.drawString(72, footer_y_position, footer_text)  # Adjust x-position if needed

            can.save()
            packet.seek(0)

            # Overlay footer on the page only if it wasn't already present
            footer_pdf = PdfReader(packet)
            page.merge_page(footer_pdf.pages[0])

        # Add the page to the writer
        writer.add_page(page)

    # Write the output PDF with corrected footer alignment
    with open(output_path, "wb") as final_pdf:
        writer.write(final_pdf)

if __name__ == "__main__":
    clean_pdf("input/KISHORE_MEDICAL_INSURANCE_BILL_2024_FINAL.pdf", "output/output.pdf")
