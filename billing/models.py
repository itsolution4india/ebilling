from django.db import models
from django.contrib.auth.models import User

class Branch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    contact = models.CharField(max_length=10)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

class Party(models.Model):
    PARTY_TYPES = [
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('both', 'Both'),
    ]
    
    PARTY_CATEGORIES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('partnership', 'Partnership'),
        ('trust', 'Trust'),
        ('fashion', 'Fashion'),
        ('appliances', 'Appliances'),
        ('electronics', 'Electronics'),
        ('groceries', 'Groceries'),
        ('other', 'Other'),
    ]

    party_name = models.CharField(max_length=255, unique=True)
    party_email = models.EmailField()
    party_address = models.TextField()
    party_contact = models.CharField(max_length=13)
    party_type = models.CharField(max_length=100, choices=PARTY_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party_gst = models.CharField(max_length=15)
    party_pan = models.CharField(max_length=10)
    party_category = models.CharField(max_length=100, choices=PARTY_CATEGORIES)
    party_ob = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Opening Balance
    party_cp = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Credit Period (in days)
    party_cl = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Credit Limit
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.party_name

    class Meta:
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'

class Product(models.Model):
    # Note: The original SQL schema seems to have party fields in products table
    # This appears to be a mistake. I'll create a proper product model
    product_name = models.CharField(max_length=255, unique=True)
    product_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    unit_of_measure = models.CharField(max_length=50, default='pcs')
    category = models.CharField(max_length=100)
    hsn_code = models.CharField(max_length=20, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        
        
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]
    
    # Basic invoice information
    name = models.CharField(max_length=255)  # Customer/Party name
    number = models.CharField(max_length=100)  # Phone number
    invoice_no = models.CharField(max_length=50, unique=True)  # Invoice number
    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # For soft delete
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Invoice #{self.invoice_no} - {self.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()  # Reference to Product ID
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product_name} - {self.invoice.invoice_no}"
    
class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('UPI', 'UPI'),
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('NetBanking', 'NetBanking'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField()
    party_name = models.CharField(max_length=255)
    party_phone = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"{self.party_name} - ₹{self.amount} ({self.payment_mode})"