from django.contrib import admin
from .models import Party, Branch, Product, Invoice, InvoiceItem

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
    
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['amount']
    fields = ['product_id', 'product_name', 'product_description', 'quantity', 'rate', 'amount']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_no', 'name', 'number', 'amount', 'status', 
        'invoice_date', 'due_date', 'created_at', 'is_active'
    ]
    list_filter = ['status', 'is_active', 'created_at', 'invoice_date', 'due_date']
    search_fields = ['invoice_no', 'name', 'number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_no', 'name', 'number')
        }),
        ('Dates', {
            'fields': ('invoice_date', 'due_date')
        }),
        ('Financial', {
            'fields': ('amount', 'status')
        }),
        ('System', {
            'fields': ('user', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'product_name', 'quantity', 'rate', 'amount', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['product_name', 'invoice__invoice_no', 'invoice__name']
    readonly_fields = ['amount', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('invoice')