from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from decimal import Decimal, InvalidOperation
from .models import Invoice, InvoiceItem
from .pdf_utils import process_invoice
from .utils import generate_invoice_number


# --- Helper to safely convert decimals ---
def safe_decimal(value, default=0):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return Decimal(default)


def index(request):
    """Render the invoice form"""
    return render(request, "invoices/index.html")


def generate(request):
    """Generate invoice, save to DB, and create PDF"""
    if request.method != "POST":
        return render(request, "invoices/index.html")

    try:
        # --- Customer & Salesman Info ---
        customer_name = request.POST.get("customer_name", "").strip()
        address = request.POST.get("address", "").strip()
        license_no = request.POST.get("license_no", "").strip()
        salesman = request.POST.get("salesman", "").strip() or "Unknown"

        # --- Items ---
        names = request.POST.getlist("item_name[]")
        qtys = request.POST.getlist("qty[]")
        prices = request.POST.getlist("price[]")
        discounts = request.POST.getlist("discount[]")
        batches = request.POST.getlist("batch[]")
        expiries = request.POST.getlist("expiry[]")

        items = []
        total = Decimal("0.00")

        for i in range(len(names)):
            qty = safe_decimal(qtys[i], 1)
            price = safe_decimal(prices[i], 0)
            disc = safe_decimal(discounts[i], 0)
            net_amount = (price - price * disc / 100) * qty
            total += net_amount

            items.append({
                "name": names[i] or f"Item {i+1}",
                "qty": qty,
                "price": price,
                "discount": disc,
                "batch": batches[i] if i < len(batches) else "",
                "expiry": expiries[i] if i < len(expiries) else "",
            })

        # --- Save invoice ---
        invoice_no = generate_invoice_number()
        invoice = Invoice.objects.create(
            customer_name=customer_name,
            address=address,
            license_no=license_no,
            # salesman=salesman,
            total_amount=total,
            invoice_no=invoice_no
            
        )

        # --- Save invoice items ---
        for item in items:
            InvoiceItem.objects.create(invoice=invoice, **item)

        # --- Generate PDF ---
        pdf = process_invoice({
            "invoice_no": invoice.invoice_no,
            "date": invoice.date.strftime("%d/%m/%Y"),
            "customer_name": invoice.customer_name,
            "address": invoice.address,
            "license_no": invoice.license_no, 
            "items": items,
        })

        return FileResponse(
            open(pdf, "rb"),
            as_attachment=True,
            filename=f"{invoice.invoice_no}.pdf"
        )

    except Exception as e:
        return HttpResponse(
            f"<h2>Error generating invoice:</h2><pre>{e}</pre>",
            status=500
        )
