from .models import Invoice

def generate_invoice_number():
    """Generate next invoice number only"""
    last_invoice = Invoice.objects.order_by("id").last()
    start_number = 380

    if not last_invoice:
        return f"HHC-{start_number:04d}"

    last_no = last_invoice.invoice_no
    if last_no and "-" in last_no:
        try:
            last_number = int(last_no.split("-")[-1])
            next_number = last_number + 1
        except ValueError:
            next_number = last_invoice.id + start_number
    else:
        next_number = last_invoice.id + start_number

    return f"HHC-{next_number:04d}"
