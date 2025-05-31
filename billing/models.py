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
    ]

    party_name = models.CharField(max_length=255, unique=True)
    party_email = models.EmailField()
    party_address = models.TextField()
    party_contact = models.CharField(max_length=13)
    party_type = models.CharField(max_length=100, choices=PARTY_TYPES)
    party_gst = models.CharField(max_length=15)
    party_pan = models.CharField(max_length=10)
    party_category = models.CharField(max_length=100, choices=PARTY_CATEGORIES)
    party_ob = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Opening Balance
    party_cp = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Credit Period
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
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'