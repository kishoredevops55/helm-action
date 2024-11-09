from docx import Document
import sys

def modify_word_doc(input_path, output_path):
    # Load the document
    doc = Document(input_path)

    # Define updates as a dictionary of replacements
    updates = {
        "Total Contribution\n1000.00": "Total Contribution\n40000.00",
        "Current Invested Amount\n1001.78": "Current Invested Amount\n40000.00",
        "Number of Contributions\n2": "Number of Contributions\n1",
        "Current Valuation\n995.41": "Current Valuation\n40000.00"
    }

    # Update paragraphs
    for para in doc.paragraphs:
        for old_text, new_text in updates.items():
            if old_text in para.text:
                para.text = para.text.replace(old_text, new_text)

    # Update table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for old_text, new_text in updates.items():
                    if old_text in cell.text:
                        cell.text = cell.text.replace(old_text, new_text)

    # Save the modified document
    doc.save(output_path)

# Run the modification based on command line arguments
if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    modify_word_doc(input_path, output_path)
