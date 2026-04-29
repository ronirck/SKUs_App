from pypdf import PdfReader
import json

def extract_sample(pdf_path, pages=3):
    try:
        reader = PdfReader(pdf_path)
        sample_text = ""
        for i in range(min(pages, len(reader.pages))):
            sample_text += f"--- PAGE {i+1} ---\n"
            sample_text += reader.pages[i].extract_text()
            sample_text += "\n"
        return sample_text
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    text = extract_sample("Eagle.pdf")
    with open("scratch/pdf_sample.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Sample extracted to scratch/pdf_sample.txt")
