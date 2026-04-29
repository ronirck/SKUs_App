import fitz

def check_fitz_page_5(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        if len(doc) >= 5:
            page = doc[4]
            text = page.get_text()
            return text if text.strip() else "[No text on page 5 with fitz]"
        return "[PDF has fewer than 5 pages]"
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(check_fitz_page_5("Eagle.pdf"))
