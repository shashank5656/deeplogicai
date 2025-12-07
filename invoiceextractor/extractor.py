# import pdfplumber
# import re

# def extract_text(pdf_path):
#     text = ""
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             t = page.extract_text() or ""
#             text += t + "\n"
#     return text


# def extract_fields(text):

#     invoice_number = ""
#     invoice_date = ""

#     seller_name = ""
#     seller_address = ""

#     buyer_name = ""
#     buyer_address = ""

#     currency = "EUR"  # Almost all invoices are EUR

#     subtotal = ""
#     tax_amount = ""
#     total_amount = ""

#     line_items = []

#     lines = text.split("\n")


#     # ---------------- INVOICE NUMBER ----------------
#     for line in lines:
#         match = re.search(r"AUFNR(\d+)", line)
#         if match:
#             invoice_number = "AUFNR" + match.group(1)
#             break


#     # ---------------- INVOICE DATE ----------------
#     for line in lines:
#         match = re.search(r"(\d{2}\.\d{2}\.\d{4})", line)
#         if match:
#             invoice_date = match.group(1)
#             break


#     # ---------------- BUYER BLOCK ----------------
#     buyer_block = []
#     found = False

#     for line in lines:
#         if "Kundenanschrift" in line:
#             found = True
#             continue
#         if found:
#             if line.strip() == "":
#                 break
#             buyer_block.append(line.strip())

#     if buyer_block:
#         buyer_name = buyer_block[0]
#         buyer_address = ", ".join(buyer_block[1:])


#     # ---------------- SELLER BLOCK ----------------
#     # Usually located near the bottom
#     last_lines = lines[-15:]

#     for idx, line in enumerate(last_lines):
#         if "GmbH" in line or "AG" in line or "KG" in line:
#             seller_name = line.strip()
#             if idx + 1 < len(last_lines):
#                 seller_address = last_lines[idx + 1].strip()
#             break


#     # ---------------- TOTALS ----------------
#     for line in lines:
#         if "Gesamtwert EUR" in line:
#             subtotal = line.split()[-1]

#         if "MwSt" in line:
#             tax_amount = line.split()[-1]

#         if "inkl. MwSt" in line:
#             total_amount = line.split()[-1]


#     # ---------------- RETURN FULL SCHEMA ----------------
#     return {
#         "invoice_number": invoice_number,
#         "invoice_date": invoice_date,

#         "seller_name": seller_name,
#         "seller_address": seller_address,

#         "buyer_name": buyer_name,
#         "buyer_address": buyer_address,

#         "currency": currency,
#         "subtotal": subtotal,
#         "tax_amount": tax_amount,
#         "total_amount": total_amount,

#         "line_items": line_items  # (Empty for now unless needed)
#     }
# invoiceextractor/extractor.py
from pathlib import Path
import json
import traceback

# --- your extraction functions (pdfplumber) ---
# If you already have them in another file, you can import instead.
import pdfplumber
import re

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text += t + "\n"
    return text

def extract_fields(text):
    invoice_number = ""
    invoice_date = ""

    seller_name = ""
    seller_address = ""

    buyer_name = ""
    buyer_address = ""

    currency = "EUR"

    subtotal = ""
    tax_amount = ""
    total_amount = ""

    line_items = []

    lines = text.split("\n")

    # invoice number
    for line in lines:
        match = re.search(r"AUFNR(\d+)", line)
        if match:
            invoice_number = "AUFNR" + match.group(1)
            break

    # invoice date
    for line in lines:
        match = re.search(r"(\d{2}\.\d{2}\.\d{4})", line)
        if match:
            invoice_date = match.group(1)
            break

    # buyer block
    buyer_block = []
    found = False
    for line in lines:
        if "Kundenanschrift" in line:
            found = True
            continue
        if found:
            if line.strip() == "":
                break
            buyer_block.append(line.strip())
    if buyer_block:
        buyer_name = buyer_block[0]
        buyer_address = ", ".join(buyer_block[1:])

    # seller block (heuristic)
    last_lines = lines[-15:]
    for idx, line in enumerate(last_lines):
        if "GmbH" in line or "AG" in line or "KG" in line:
            seller_name = line.strip()
            if idx + 1 < len(last_lines):
                seller_address = last_lines[idx + 1].strip()
            break

    # totals (heuristic)
    for line in lines:
        if "Gesamtwert EUR" in line:
            subtotal = line.split()[-1]
        if "MwSt" in line:
            tax_amount = line.split()[-1]
        if "inkl. MwSt" in line:
            total_amount = line.split()[-1]

    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "seller_name": seller_name,
        "seller_address": seller_address,
        "buyer_name": buyer_name,
        "buyer_address": buyer_address,
        "currency": currency,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "line_items": line_items
    }

# --- wrapper the CLI expects ---------------------------------
def extract_folder(pdf_dir, output):
    """
    Called by invoice_qc CLI.
    Reads all PDFs in pdf_dir, extracts text+fields using above functions,
    and writes a JSON array to output.
    """
    pdf_dir = Path(pdf_dir)
    results = []

    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF dir not found: {pdf_dir}")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    for pdf_path in pdf_files:
        try:
            text = extract_text(str(pdf_path))
            fields = extract_fields(text)
            # attach metadata
            fields.update({
                "filename": pdf_path.name,
                "path": str(pdf_path),
                "text_snippet": (text[:1000] if text else "")
            })
            results.append(fields)
        except Exception:
            # keep processing remaining PDFs even on error
            results.append({
                "filename": pdf_path.name,
                "path": str(pdf_path),
                "error": traceback.format_exc()
            })

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(results)} records to {output}")
    return results

# aliases CLI checks for
extract_pdfs = extract_folder
extract_all = extract_folder
extract = extract_folder
main = extract_folder
