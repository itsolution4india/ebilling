from rest_framework import serializers
from .models import Party, Branch, Product, Invoice, InvoiceItem, Payment

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        
class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'product_id', 'product_name', 'product_description', 
                 'quantity', 'rate', 'amount', 'created_at']
        read_only_fields = ['id', 'amount', 'created_at']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = ['id', 'name', 'number', 'invoice_no', 'invoice_date', 
                 'due_date', 'amount', 'status', 'created_at', 'updated_at', 
                 'user', 'is_active', 'items']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)
        
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        return invoice
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items - delete existing and create new ones
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)
        
        return instance

class InvoiceListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'name', 'number', 'invoice_no', 'invoice_date', 
            'due_date', 'amount', 'status', 'created_at', 'items_count',
            'user_id'
        ]

    def get_items_count(self, obj):
        return obj.items.count()
    
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'date',
            'party_name',
            'party_phone',
            'amount',
            'payment_mode',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def validate_payment_mode(self, value):
        valid_modes = ['UPI', 'Cash', 'Card', 'NetBanking', 'Bank Transfer', 'Cheque']
        if value not in valid_modes:
            raise serializers.ValidationError("Invalid payment mode")
        return value