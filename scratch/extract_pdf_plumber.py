import pdfplumber

def extract_sample_plumber(pdf_path, pages=3):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i in range(min(pages, len(pdf.pages))):
                text += f"--- PAGE {i+1} ---\n"
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text += page_text
                else:
                    text += "[No text found on this page]\n"
                text += "\n"
        return text
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    text = extract_sample_plumber("Eagle.pdf")
    with open("scratch/pdf_sample_plumber.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Sample extracted to scratch/pdf_sample_plumber.txt")
