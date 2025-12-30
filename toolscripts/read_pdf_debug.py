
import os
from pypdf import PdfReader

def read_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        # Read first 5 pages and last 5 pages to get a gist, or all if small
        # Let's read the first 10 pages to capture the architecture sections usually at the start
        pages_to_read = min(len(reader.pages), 15)
        print(f"--- Reading {file_path} ({len(reader.pages)} pages) - First {pages_to_read} pages ---")
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        return f"Error reading {file_path}: {e}"


if __name__ == "__main__":
    files = [
        r"c:\Users\Kandukoori Tejaswini\NDRA-PII\NDRA\devdocs\NDRA-PII Technical Documentation.pdf",
        r"c:\Users\Kandukoori Tejaswini\NDRA-PII\NDRA\devdocs\ndrapiichatgptconvo.pdf"
    ]

    output_text = ""
    for f in files:
        output_text += read_pdf(f)
        output_text += "\n" + "="*50 + "\n"
    
    with open("pdf_debug_output.txt", "w", encoding="utf-8") as f:
        f.write(output_text)

    print("Done writing to pdf_debug_output.txt")

