import fitz
import os
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime

BASE_DIR = settings.BASE_DIR
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# PDF template file
ORIGINAL_PDF = os.path.join(UPLOAD_FOLDER, "original.pdf")

# Header coordinates in the PDF template
HEADER_COORDS = {
    "customer_name": (125.84, 110.15, 272.87, 122.43),
    "address": (125.84, 124.65, 347.06, 134.70),
    "invoice_no": (482.60, 110.13, 524.41, 120.18),
    "date": (479.85, 120.98, 523.99, 131.03),
    "license_no": (75.06, 181.90, 173.89, 191.95),
}

# 🔹 SALESMAN COORDINATES
# SALESMAN_VALUE_RECT = (479.799, 146.184, 519.003, 156.237)

GROSS_VALUE_RECT = (540.85, 265.344, 567.877, 275.397)

# Table column X positions
TABLE_COLS = {
    "sr": 54.7,
    "name": 72.1,
    "qty": 208.5,
    "batch": 249.7,
    "expiry": 330.3,
    "price": 388.6,
    "discount": 505.6,
    "amount": 546.0,
}

ROW_START_Y = 221.4
ROW_HEIGHT = 9.5

# Totals and payable rectangles
NET_PAYABLE_WIPE_RECT = (530.0, 323.0, 580.0, 340.0)
PAYABLE_RECT = (540.84, 325.49, 567.87, 336.66)
TOTAL_RECT = (539.33, 242.04, 573.66, 252.09)
DISCOUNT_AMOUNT_RECT = (567.85, 277.34, 590.85, 287.39)

# Wipe (white out) a rectangle area in PDF
def wipe_rect(page, rect):
    r = fitz.Rect(rect)
    page.add_redact_annot(r, fill=(1, 1, 1))
    page.apply_redactions()

# Write text into a rectangle
def write_in_rect(page, rect, text, fontsize=8):
    r = fitz.Rect(rect)
    page.insert_text(
        (r.x0 + 1, r.y1 - 2),
        str(text),
        fontsize=fontsize,
        fontname="helv"
    )

# Main function to process invoice
def process_invoice(data):
    if not os.path.exists(ORIGINAL_PDF):
        raise FileNotFoundError("Original PDF template not found in 'uploads/' folder.")

    data["date"] = localtime(timezone.now()).strftime("%d-%m-%Y") 
    print(data)  

    doc = fitz.open(ORIGINAL_PDF)
    page = doc[0]

    # Write header info
    for key, rect in HEADER_COORDS.items():
        wipe_rect(page, rect)
        write_in_rect(page, rect, data.get(key, ""), fontsize=8.5)

    # 🔹 SALESMAN NAME (HTML FORM → PDF)
    # salesman_name = data.get("salesman", "").strip() or "N/A"
    # wipe_rect(page, SALESMAN_VALUE_RECT)
    # write_in_rect(page, SALESMAN_VALUE_RECT, salesman_name, fontsize=8.5)

    # Wipe table area
    table_rect = fitz.Rect(
        50, ROW_START_Y - 2,
        580, ROW_START_Y + len(data["items"]) * ROW_HEIGHT + 2
    )
    wipe_rect(page, table_rect)

    total_gross = Decimal("0.00")
    total_discount = Decimal("0.00")
    total_net = Decimal("0.00")

    for i, item in enumerate(data["items"]):
        y = ROW_START_Y + i * ROW_HEIGHT

        qty = Decimal(item["qty"])
        price = Decimal(item["price"])
        disc = Decimal(item["discount"])

        gross = price * qty
        discount_amount = gross * disc / Decimal("100.00")
        net_amount = gross - discount_amount

        total_gross += gross
        total_discount += discount_amount
        total_net += net_amount

        page.insert_text((TABLE_COLS["sr"], y), str(i + 1), fontsize=8)
        page.insert_text((TABLE_COLS["name"], y), item["name"], fontsize=8)
        page.insert_text((TABLE_COLS["qty"], y), str(qty), fontsize=8)
        page.insert_text((TABLE_COLS["batch"], y), item["batch"], fontsize=8)
        page.insert_text((TABLE_COLS["expiry"], y), item["expiry"], fontsize=8)
        page.insert_text((TABLE_COLS["price"], y), f"{price:.2f}", fontsize=8)
        page.insert_text((TABLE_COLS["discount"], y), f"{disc}%", fontsize=8)
        page.insert_text((TABLE_COLS["amount"], y), f"{net_amount:.2f}", fontsize=8)

    # Write totals
    wipe_rect(page, TOTAL_RECT)
    write_in_rect(page, TOTAL_RECT, f"{total_gross:.2f}", fontsize=9)

    wipe_rect(page, GROSS_VALUE_RECT)
    write_in_rect(page, GROSS_VALUE_RECT, f"{total_gross:.2f}", fontsize=9)

    wipe_rect(page, DISCOUNT_AMOUNT_RECT)
    write_in_rect(page, DISCOUNT_AMOUNT_RECT, f"{total_discount:.2f}", fontsize=9)

    wipe_rect(page, NET_PAYABLE_WIPE_RECT)
    write_in_rect(page, PAYABLE_RECT, f"{total_net:.2f}", fontsize=9)

    invoice_no_safe = "".join(c for c in data["invoice_no"] if c.isalnum())
    output_path = os.path.join(OUTPUT_FOLDER, f"Invoice_{invoice_no_safe}.pdf")

    doc.save(output_path)
    doc.close()
    return output_path
