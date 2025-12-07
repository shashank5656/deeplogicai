# #!/usr/bin/env python3
# """
# Simple CLI for invoice-qc:
# Commands:
#   extract      - (optional) run extractor to produce JSON
#   validate     - validate an extracted JSON file
#   full-run     - extract (if extractor available) then validate
# """

# import argparse
# import json
# import os
# import sys

# from invoice_qc import validator

# # Try to import an extractor if present in invoiceextractor.extractor or invoice_qc.extractor
# EXTRACTOR_AVAILABLE = False
# extractor_module = None
# for mod_name in ("invoiceextractor.extractor", "invoice_qc.extractor", "extractor"):
#     try:
#         extractor_module = __import__(mod_name, fromlist=["*"])
#         EXTRACTOR_AVAILABLE = True
#         break
#     except Exception:
#         extractor_module = None

# def run_extract(pdf_dir: str, output: str):
#     """
#     Try to call the project's extractor if available.
#     If not available, print helpful message.
#     Expected extractor API (best-effort): extractor.extract_folder(pdf_dir, output_json_path)
#     """
#     if not EXTRACTOR_AVAILABLE or extractor_module is None:
#         print("No extractor module found. Please run your extractor script separately.")
#         print("Look for an 'extractor.py' in invoiceextractor/ or invoice_qc/ and run it to produce JSON.")
#         return False

#     # Best-effort: try common function names
#     for fn in ("extract_folder", "extract_pdfs", "extract_all", "extract"):
#         if hasattr(extractor_module, fn):
#             func = getattr(extractor_module, fn)
#             print(f"Running extractor.{fn}('{pdf_dir}', '{output}')")
#             try:
#                 func(pdf_dir, output)
#                 return True
#             except Exception as e:
#                 print("Extractor function executed but raised an error:", e)
#                 return False

#     # Fallback: try a function named "main"
#     if hasattr(extractor_module, "main"):
#         try:
#             print(f"Running extractor.main('{pdf_dir}', '{output}')")
#             extractor_module.main(pdf_dir, output)
#             return True
#         except Exception as e:
#             print("Extractor.main raised error:", e)
#             return False

#     print("Extractor module loaded but no compatible function found (checked: extract_folder, extract_pdfs, extract_all, extract, main).")
#     return False


# def run_validate(input_json: str, report_out: str):
#     if not os.path.exists(input_json):
#         print("Input file does not exist:", input_json)
#         return 2

#     with open(input_json, "r", encoding="utf-8") as f:
#         try:
#             invoices = json.load(f)
#         except Exception as e:
#             print("Failed to parse input JSON:", e)
#             return 3

#     results = validator.validate_invoices(invoices)

#     with open(report_out, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2, default=str)

#     # print short summary
#     s = results["summary"]
#     print(f"Total: {s['total_invoices']}, Valid: {s['valid_invoices']}, Invalid: {s['invalid_invoices']}")
#     top_errors = sorted(s.get("error_counts", {}).items(), key=lambda x: -x[1])[:5]
#     if top_errors:
#         print("Top errors:")
#         for e, c in top_errors:
#             print(f"  {e}: {c}")
#     else:
#         print("No errors.")
#     # exit code non-zero if any invalid
#     return 0 if s["invalid_invoices"] == 0 else 4


# def main():
#     parser = argparse.ArgumentParser(prog="invoice-qc", description="Invoice QC CLI")
#     sub = parser.add_subparsers(dest="cmd", required=True)

#     p_extract = sub.add_parser("extract", help="Run PDF extractor to produce JSON")
#     p_extract.add_argument("--pdf-dir", required=True, help="Folder containing PDFs")
#     p_extract.add_argument("--output", required=True, help="Output JSON path")

#     p_validate = sub.add_parser("validate", help="Validate extracted JSON")
#     p_validate.add_argument("--input", required=True, help="Input JSON (list of invoices)")
#     p_validate.add_argument("--report", required=True, help="Output validation report JSON")

#     p_full = sub.add_parser("full-run", help="Extract (if possible) then validate")
#     p_full.add_argument("--pdf-dir", required=True, help="Folder containing PDFs")
#     p_full.add_argument("--output-json", required=True, help="Output extracted JSON")
#     p_full.add_argument("--report", required=True, help="Output validation report JSON")

#     args = parser.parse_args()

#     if args.cmd == "extract":
#         ok = run_extract(args.pdf_dir, args.output)
#         sys.exit(0 if ok else 1)

#     if args.cmd == "validate":
#         code = run_validate(args.input, args.report)
#         sys.exit(code)

#     if args.cmd == "full-run":
#         # try extract
#         ok = run_extract(args.pdf_dir, args.output_json)
#         if not ok:
#             print("Extractor step failed or not available; aborting full-run.")
#             sys.exit(2)
#         code = run_validate(args.output_json, args.report)
#         sys.exit(code)


# if __name__ == "__main__":
#     main()
#!/usr/bin/env python3
"""
Simple CLI for invoice-qc:
Commands:
  extract        - run extractor on custom paths
  validate       - validate JSON using custom paths
  full-run       - extract + validate using custom paths

  short-extract  - extract using default paths
  short-validate - validate using default paths
  short-full     - extract + validate using default paths
"""

import argparse
import json
import os
import sys

from invoice_qc import validator

# Try to import extractor
EXTRACTOR_AVAILABLE = False
extractor_module = None
for mod_name in ("invoiceextractor.extractor", "invoice_qc.extractor", "extractor"):
    try:
        extractor_module = __import__(mod_name, fromlist=["*"])
        EXTRACTOR_AVAILABLE = True
        break
    except Exception:
        extractor_module = None


def run_extract(pdf_dir: str, output: str):
    if not EXTRACTOR_AVAILABLE or extractor_module is None:
        print("No extractor module found.")
        return False

    for fn in ("extract_folder", "extract_pdfs", "extract_all", "extract"):
        if hasattr(extractor_module, fn):
            func = getattr(extractor_module, fn)
            print(f"Running extractor.{fn}('{pdf_dir}', '{output}')")
            try:
                func(pdf_dir, output)
                return True
            except Exception as e:
                print("Extractor error:", e)
                return False

    if hasattr(extractor_module, "main"):
        try:
            extractor_module.main(pdf_dir, output)
            return True
        except Exception as e:
            print("Extractor.main error:", e)
            return False

    print("Extractor found, but no compatible function.")
    return False


def run_validate(input_json: str, report_out: str):
    if not os.path.exists(input_json):
        print("Input JSON does not exist:", input_json)
        return 2

    with open(input_json, "r", encoding="utf-8") as f:
        try:
            invoices = json.load(f)
        except Exception as e:
            print("Failed to parse JSON:", e)
            return 3

    results = validator.validate_invoices(invoices)

    with open(report_out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    
    s = results["summary"]
    print(f"Total: {s['total_invoices']}, Valid: {s['valid_invoices']}, Invalid: {s['invalid_invoices']}")
    return 0 if s["invalid_invoices"] == 0 else 4


def main():
    parser = argparse.ArgumentParser(prog="invoice-qc", description="Invoice QC CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="Run PDF extractor")
    p_extract.add_argument("--pdf-dir", required=True)
    p_extract.add_argument("--output", required=True)

    p_validate = sub.add_parser("validate", help="Validate extracted JSON")
    p_validate.add_argument("--input", required=True)
    p_validate.add_argument("--report", required=True)

    p_full = sub.add_parser("full-run", help="Extract then validate")
    p_full.add_argument("--pdf-dir", required=True)
    p_full.add_argument("--output-json", required=True)
    p_full.add_argument("--report", required=True)

    sub.add_parser("short-extract", help="Extract using default paths")
    sub.add_parser("short-validate", help="Validate using default paths")
    sub.add_parser("short-full", help="Extract + validate using default paths")

    args = parser.parse_args()

  
    if args.cmd == "short-extract":
        return sys.exit(0 if run_extract("samplespdf", "output.json") else 1)

    if args.cmd == "short-validate":
        return sys.exit(run_validate("output.json", "report.json"))

    if args.cmd == "short-full":
        ok = run_extract("samplespdf", "output.json")
        if not ok:
            print("Extractor failed.")
            return sys.exit(2)
        return sys.exit(run_validate("output.json", "report.json"))


    if args.cmd == "extract":
        ok = run_extract(args.pdf_dir, args.output)
        return sys.exit(0 if ok else 1)

    if args.cmd == "validate":
        return sys.exit(run_validate(args.input, args.report))

    if args.cmd == "full-run":
        ok = run_extract(args.pdf_dir, args.output_json)
        if not ok:
            print("Extractor step failed.")
            return sys.exit(2)
        return sys.exit(run_validate(args.output_json, args.report))


if __name__ == "__main__":
    main()
