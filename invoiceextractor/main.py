from extractor import extract_text, extract_fields
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_path>")
        return

    pdf_path = sys.argv[1]

    # Extract raw text
    text = extract_text(pdf_path)

    # Extract structured fields
    data = extract_fields(text)

    print("\n=== INVOICE DATA ===")
    for key, value in data.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
