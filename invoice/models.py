from django.db import models
from django.utils import timezone

class Invoice(models.Model):
    invoice_no = models.CharField(max_length=30, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    address = models.TextField()
    license_no = models.CharField(max_length=100)
    # salesman = models.CharField(max_length=200, default="Unknown")

    
    date = models.DateField(default=timezone.now, editable=False)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto invoice number ONLY
        if not self.invoice_no:
            last_invoice = Invoice.objects.order_by("id").last()
            start_number = 380

            if not last_invoice:
                self.invoice_no = f"HHC-{start_number:04d}"
            else:
                try:
                    last_number = int(last_invoice.invoice_no.split("-")[-1])
                    self.invoice_no = f"HHC-{last_number + 1:04d}"
                except Exception:
                    self.invoice_no = f"HHC-{last_invoice.id + start_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_no


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    qty = models.IntegerField()
    batch = models.CharField(max_length=50)
    expiry = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
