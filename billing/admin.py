from django.contrib import admin
from .models import Party, Branch, Product

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['party_name', 'party_email', 'party_type', 'party_category', 'status', 'created_at']
    list_filter = ['party_type', 'party_category', 'status']
    search_fields = ['party_name', 'party_email', 'party_gst', 'party_pan']
    ordering = ['-created_at']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'contact']
    ordering = ['-created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'product_code', 'unit_price', 'stock_quantity', 'status', 'created_at']
    list_filter = ['category', 'status']
    search_fields = ['product_name', 'product_code', 'hsn_code']
    ordering = ['-created_at']