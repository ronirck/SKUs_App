import pdfplumber

def check_words_page_5(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) >= 5:
                words = pdf.pages[4].extract_words()
                return words[:10] if words else "[No words on page 5]"
            return "[PDF has fewer than 5 pages]"
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(check_words_page_5("Eagle.pdf"))
