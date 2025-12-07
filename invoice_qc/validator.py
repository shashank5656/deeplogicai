import json
from collections import Counter
from invoice_qc.utils import parse_date, parse_amount, normalize_text


REQUIRED_FIELDS = ["invoice_number", "invoice_date", "seller_name", "buyer_name", "total_amount"]

SUPPORTED_CURRENCIES = {"INR", "USD", "EUR"}

TOLERANCE = 0.5 


def validate_single_invoice(inv):
    errors = []
    warnings = []

  
    for field in REQUIRED_FIELDS:
        if not inv.get(field):
            errors.append(f"missing_field: {field}")

    parsed_date = parse_date(inv.get("invoice_date"))
    if parsed_date is None:
        errors.append("invalid_date_format")


    subtotal = parse_amount(inv.get("subtotal"))
    tax = parse_amount(inv.get("tax_amount"))
    total = parse_amount(inv.get("total_amount"))

    if subtotal is None or tax is None or total is None:
        errors.append("unparseable_amount")

    if subtotal is not None and tax is not None and total is not None:
        if abs((subtotal + tax) - total) > TOLERANCE:
            errors.append("totals_mismatch")

  
    line_items = inv.get("line_items", [])
    if line_items:
        sum_line = 0
        for li in line_items:
            lt = parse_amount(li.get("line_total"))
            if lt is None:
                warnings.append("line_item_unparseable")
            else:
                sum_line += lt

        if subtotal is not None and abs(sum_line - subtotal) > TOLERANCE:
            errors.append("line_items_total_mismatch")

    return {
        "invoice_id": inv.get("invoice_number"),
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def detect_duplicates(invoices):
    seen = {}
    duplicates = []

    for idx, inv in enumerate(invoices):
        key = (
            normalize_text(inv.get("invoice_number")),
            normalize_text(inv.get("seller_name")),
            normalize_text(inv.get("invoice_date")),
        )

        if key in seen:
            duplicates.append([seen[key], idx])
        else:
            seen[key] = idx
    return duplicates


def validate_invoices(invoices):
    results = [validate_single_invoice(inv) for inv in invoices]

    dups = detect_duplicates(invoices)
    for grp in dups:
        for idx in grp:
            results[idx]["errors"].append("duplicate_invoice")
            results[idx]["is_valid"] = False


    error_counter = Counter()
    for r in results:
        for e in r["errors"]:
            error_counter[e] += 1

    summary = {
        "total_invoices": len(results),
        "valid_invoices": sum(1 for r in results if r["is_valid"]),
        "invalid_invoices": sum(1 for r in results if not r["is_valid"]),
        "error_counts": dict(error_counter)
    }

    return {"per_invoice": results, "summary": summary}



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    report = validate_invoices(data)

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print("Validation complete.")
    print(report["summary"])
