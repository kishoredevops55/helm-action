from docx import Document
import re
import sys

def modify_word_doc(input_path, output_path):
    # Load the document
    doc = Document(input_path)

    # Define updates as a dictionary of replacements with regex patterns for more flexibility
    updates = {
        r"Total Contribution\s*\n?\s*1000\.00": "Total Contribution\n40000.00",
        r"Current Invested Amount\s*\n?\s*1001\.78": "Current Invested Amount\n40000.00",
        r"Number of Contributions\s*\n?\s*2": "Number of Contributions\n1",
        r"Current Valuation\s*\n?\s*995\.41": "Current Valuation\n40000.00"
    }

    # Update paragraphs with regex matching
    for para in doc.paragraphs:
        for pattern, replacement in updates.items():
            if re.search(pattern, para.text):
                para.text = re.sub(pattern, replacement, para.text)

    # Update table cells with regex matching
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for pattern, replacement in updates.items():
                    if re.search(pattern, cell.text):
                        cell.text = re.sub(pattern, replacement, cell.text)

    # Save the modified document
    doc.save(output_path)

# Run the modification based on command line arguments
if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    modify_word_doc(input_path, output_path)
