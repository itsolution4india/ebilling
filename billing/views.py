from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Party, Product, Invoice, InvoiceItem, Payment, TotalBalance,Sales_invoice_settings,UserAccess
from .serializers import PartySerializer, ProductSerializer, InvoiceSerializer, InvoiceListSerializer, InvoiceItemSerializer, PaymentSerializer
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from decimal import Decimal, ROUND_HALF_UP
from rest_framework.permissions import AllowAny
import random
import string
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from .forms import ReturnInvoiceForm, PartyForm
import uuid
from django.http import JsonResponse
from decimal import Decimal
from django.db import transaction

import csv
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear

logger = logging.getLogger('django')

@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def login_view(request):
    """Login endpoint"""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return Response({'error': 'Invalid JSON'}, status=400)

    username = data.get('username')
    password = data.get('password')
    logger.info(f"{username}, {password}")

    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return Response({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username
        })
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

# Party Views
@api_view(['GET'])
@permission_classes([AllowAny])
def party_list(request):
    """Get all parties with optional search"""
    party_name = request.GET.get('party_name', '')
    
    parties = Party.objects.filter(status=True)
    if party_name:
        parties = parties.filter(party_name__icontains=party_name)
    
    serializer = PartySerializer(parties, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def party_store(request):
    """Create a new party"""
    data = request.data.copy()
    
    # Handle user field - expect user_id from frontend
    if 'user_id' in data:
        data['user'] = data.pop('user_id')
    
    serializer = PartySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def party_edit(request, party_id):
    """Get party details for editing"""
    try:
        party = Party.objects.get(id=party_id)
        serializer = PartySerializer(party)
        return Response(serializer.data)
    except Party.DoesNotExist:
        return Response({'error': 'Party not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([AllowAny])
def party_update(request, party_id):
    """Update party details"""
    try:
        party = Party.objects.get(id=party_id)
        data = request.data.copy()
        
        # Handle user field
        if 'user_id' in data:
            data['user'] = data.pop('user_id')
            
        serializer = PartySerializer(party, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Party.DoesNotExist:
        return Response({'error': 'Party not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def party_delete(request, party_id):
    """Delete a party (soft delete by setting status to False)"""
    try:
        party = Party.objects.get(id=party_id)
        party.status = False
        party.save()
        return Response({'message': 'Party deleted successfully'})
    except Party.DoesNotExist:
        return Response({'error': 'Party not found'}, status=status.HTTP_404_NOT_FOUND)

# Product Views
@api_view(['GET'])
@permission_classes([AllowAny])
def api_product_list(request):
    """Get all products"""
    products = Product.objects.filter(status=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def product_store(request):
    """Create a new product"""
    data = request.data.copy()
    
    # Handle user field - expect user_id from frontend or user from authenticated request
    if 'user_id' in data:
        data['user'] = data.pop('user_id')
    elif hasattr(request, 'user') and request.user.is_authenticated:
        data['user'] = request.user.id
    
    serializer = ProductSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def product_edit(request, product_id):
    """Get product details for editing"""
    try:
        product = Product.objects.get(id=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def product_delete(request, product_id):
    """Delete a product (soft delete by setting status to False)"""
    try:
        product = Product.objects.get(id=product_id)
        product.status = False
        product.save()
        return Response({'message': 'Product deleted successfully'})
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
# Invoice Views
@api_view(['GET'])
@permission_classes([AllowAny])
def api_invoice_list(request):
    """Get all invoices with optional filtering"""
    invoices = Invoice.objects.filter(is_active=True)
    
    # Optional filtering
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    if search:
        invoices = invoices.filter(
            Q(name__icontains=search) |
            Q(invoice_no__icontains=search) |
            Q(number__icontains=search)
        )
    
    serializer = InvoiceListSerializer(invoices, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def invoice_store(request):
    """Create a new invoice with optional user assignment and auto invoice number"""
    data = request.data.copy()

    # Assign user if user_id is provided or if user is authenticated
    user_id = data.get('user_id')
    if user_id:
        data['user'] = user_id
    elif request.user and request.user.is_authenticated:
        data['user'] = request.user.id
        
    if not data.get('invoice_no'):
        data['invoice_no'] = generate_random_invoice_id()

    serializer = InvoiceSerializer(data=data)
    if serializer.is_valid():
        invoice = serializer.save()
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def generate_random_invoice_id():
    """Generate a random invoice ID in format like HDHDJ736378"""
    # Generate 5 random uppercase letters
    letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    # Generate 6 random digits
    numbers = ''.join(random.choices(string.digits, k=6))
    # Combine letters and numbers
    invoice_id = letters + numbers
    
    # Check if this ID already exists in database
    from .models import Invoice  # Import your Invoice model
    while Invoice.objects.filter(invoice_no=invoice_id).exists():
        # If it exists, generate a new one
        letters = ''.join(random.choices(string.ascii_uppercase, k=5))
        numbers = ''.join(random.choices(string.digits, k=6))
        invoice_id = letters + numbers
    
    return invoice_id

# Alternative function if you want different format patterns
def generate_random_invoice_id_mixed():
    """Generate a random invoice ID with mixed pattern like HD7DJ736H78"""
    chars = string.ascii_uppercase + string.digits
    invoice_id = ''.join(random.choices(chars, k=11))
    
    # Ensure uniqueness
    from .models import Invoice
    while Invoice.objects.filter(invoice_no=invoice_id).exists():
        invoice_id = ''.join(random.choices(chars, k=11))
    
    return invoice_id

@api_view(['GET'])
@permission_classes([AllowAny])
def api_invoice_detail(request, invoice_id):
    """Get invoice details"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def invoice_edit(request, invoice_id):
    """Get invoice details for editing"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([AllowAny])
def api_invoice_update(request, invoice_id):
    """Update invoice details"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        data = request.data.copy()
        
        # Handle user field
        if 'user_id' in data:
            data['user'] = data.pop('user_id')
            
        serializer = InvoiceSerializer(invoice, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def api_invoice_delete(request, invoice_id):
    """Delete an invoice (soft delete by setting is_active to False)"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        invoice.is_active = False
        invoice.save()
        return Response({'message': 'Invoice deleted successfully'})
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([AllowAny])
def invoice_status_update(request, invoice_id):
    """Update invoice status (paid/unpaid)"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        new_status = request.data.get('status')
        
        if new_status not in ['paid', 'unpaid']:
            return Response({'error': 'Invalid status. Must be "paid" or "unpaid"'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        invoice.status = new_status
        invoice.save()
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

# Invoice Items Views
@api_view(['GET'])
@permission_classes([AllowAny])
def invoice_items(request, invoice_id):
    """Get all items for a specific invoice"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        items = invoice.items.all()
        serializer = InvoiceItemSerializer(items, many=True)
        return Response(serializer.data)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def invoice_item_add(request, invoice_id):
    """Add an item to an invoice"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        data = request.data.copy()
        data['invoice'] = invoice.id
        
        serializer = InvoiceItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            
            # Recalculate invoice total
            total_amount = sum(item.amount for item in invoice.items.all())
            invoice.amount = total_amount
            invoice.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def invoice_item_delete(request, invoice_id, item_id):
    """Delete an item from an invoice"""
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_active=True)
        item = invoice.items.get(id=item_id)
        item.delete()
        
        # Recalculate invoice total
        total_amount = sum(item.amount for item in invoice.items.all())
        invoice.amount = total_amount
        invoice.save()
        
        return Response({'message': 'Item deleted successfully'})
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
    except InvoiceItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
    
# Payment Views
@api_view(['GET'])
@permission_classes([AllowAny])
def payment_list(request):
    """Get all payments"""
    payments = Payment.objects.filter(status=True)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def payment_store(request):
    """Create a new payment record"""
    data = request.data.copy()
    
    # Handle user field - expect user_id from frontend or user from authenticated request
    if 'user_id' in data:
        data['user'] = data.pop('user_id')
    elif hasattr(request, 'user') and request.user.is_authenticated:
        data['user'] = request.user.id
    else:
        # For demo purposes, using user id 1 if no user specified
        # In production, you should handle authentication properly
        data['user'] = 1
    
    serializer = PaymentSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def payment_edit(request, payment_id):
    """Get payment details for editing"""
    try:
        payment = Payment.objects.get(id=payment_id)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([AllowAny])
def payment_update(request, payment_id):
    """Update payment details"""
    try:
        payment = Payment.objects.get(id=payment_id)
        data = request.data.copy()
        
        # Handle user field
        if 'user_id' in data:
            data['user'] = data.pop('user_id')
            
        serializer = PaymentSerializer(payment, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def payment_delete(request, payment_id):
    """Delete a payment (soft delete by setting status to False)"""
    try:
        payment = Payment.objects.get(id=payment_id)
        payment.status = False
        payment.save()
        return Response({'message': 'Payment deleted successfully'})
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def payment_by_party(request, party_name):
    """Get all payments for a specific party"""
    payments = Payment.objects.filter(party_name__icontains=party_name, status=True)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def payment_statistics(request):
    """Get payment statistics"""
    from django.db.models import Sum, Count
    
    total_amount = Payment.objects.filter(status=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_count = Payment.objects.filter(status=True).count()
    
    # Payment mode wise statistics
    payment_modes = Payment.objects.filter(status=True).values('payment_mode').annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    return Response({
        'total_amount': total_amount,
        'total_count': total_count,
        'payment_modes': payment_modes
    })
    
def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

def check_user_permission(user, permission):
    """Helper function to check a specific permission for a user."""
    try:
        user_access = UserAccess.objects.get(user=user)
        return getattr(user_access, permission, False)
    except UserAccess.DoesNotExist:
        return False

@login_required
def dashboard(request):
    user = request.user
    if not check_user_permission(request.user, 'can_view_dashboard'):
           return redirect("access_denide")

    
    # Existing calculations
    to_collect = Invoice.objects.filter(user=user,status='unpaid').aggregate(total=Sum('amount'))['total'] or 0
    to_pay = Payment.objects.filter(user=user,).aggregate(total=Sum('amount'))['total'] or 0
    stock_value = Product.objects.filter(user=user).aggregate(
        total=Sum(F('stock_quantity') * F('unit_price'))
    )['total'] or 0
    total_balance = TotalBalance.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0

    invoices = Invoice.objects.filter(user=user).order_by('-invoice_date')[:10]  # Latest 10 invoices
    payments = Payment.objects.filter(user=user).order_by('-date')[:10]  # Latest 10 payments

    # Chart filtering logic
    chart_filter = request.GET.get('chart_filter', 'daily')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default date range (last 6 months)
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Filter invoices by date range and user
    invoice_queryset = Invoice.objects.filter(
        user=user,
        invoice_date__range=[start_date, end_date]
    )

    # Group data based on filter type
    if chart_filter == 'daily':
        chart_data = invoice_queryset.extra(
            select={'period': "DATE(invoice_date)"}
        ).values('period').annotate(
            total_amount=Sum('amount')
        ).order_by('period')
        
    elif chart_filter == 'weekly':
        chart_data = invoice_queryset.annotate(
            period=TruncWeek('invoice_date')
        ).values('period').annotate(
            total_amount=Sum('amount')
        ).order_by('period')
        
    elif chart_filter == 'monthly':
        chart_data = invoice_queryset.annotate(
            period=TruncMonth('invoice_date')
        ).values('period').annotate(
            total_amount=Sum('amount')
        ).order_by('period')
        
    elif chart_filter == 'yearly':
        chart_data = invoice_queryset.annotate(
            period=TruncYear('invoice_date')
        ).values('period').annotate(
            total_amount=Sum('amount')
        ).order_by('period')

    # Prepare chart data for JavaScript
    chart_labels = []
    chart_values = []
    
    for item in chart_data:
        if chart_filter == 'daily':
            chart_labels.append(str(item['period']))
        elif chart_filter == 'weekly':
            chart_labels.append(item['period'].strftime('%Y-W%U'))
        elif chart_filter == 'monthly':
            chart_labels.append(item['period'].strftime('%Y-%m'))
        elif chart_filter == 'yearly':
            chart_labels.append(item['period'].strftime('%Y'))
            
        # Convert Decimal to float for JSON serialization
        amount = float(item['total_amount']) if item['total_amount'] else 0
        chart_values.append(amount)

    # Calculate total sales for the period
    total_sales = sum(chart_values)

    context = {
        'to_collect': to_collect,
        'to_pay': to_pay,
        'stock_value': stock_value,
        'total_balance': total_balance,
        'invoices': invoices,
        'payments': payments,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'chart_filter': chart_filter,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_sales': total_sales,
    }

    return render(request, 'dashboard.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('login-page')

# Auto-generate code
def generate_product_code():
    return f"PROD-{uuid.uuid4().hex[:8].upper()}"

def generate_hsn_code():
    return f"HSN-{uuid.uuid4().hex[:6].upper()}"

@login_required
def product_list(request):
    if not check_user_permission(request.user, 'can_view_items'):
           return redirect("access_denide")
    
    access=UserAccess.objects.get(user=request.user)

    products = Product.objects.filter(user=request.user)

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        products = products.filter(category=category_filter)

    categories = Product.objects.filter(user=request.user).exclude(category__isnull=True).exclude(category__exact='').values_list('category', flat=True).distinct()

    context = {
        'products': products,
        'category_filter': category_filter,
        'categories': categories,
        'access':access
    }
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    invoice_items = InvoiceItem.objects.filter(product_id=product.pk, invoice__user=request.user).select_related('invoice')
    
    party_prices = []
    for item in invoice_items:
        party_prices.append({
            'party_name': item.invoice.name,
            'invoice_no': item.invoice.invoice_no,
            'rate': item.rate,
            'quantity': item.quantity,
            'date': item.invoice.invoice_date,
        })

    return render(request, 'products/product_detail.html', {
        'product': product,
        'party_prices': party_prices
    })

@login_required
def update_product_barcode(request, product_id):
    """
    Update the barcode for a specific product
    """
    try:
        product = get_object_or_404(Product, pk=product_id, user=request.user)
        
        # Parse JSON data from request
        data = json.loads(request.body)
        new_barcode_id = data.get('barcode_id', '').strip()
        
        if not new_barcode_id:
            return JsonResponse({
                'success': False,
                'message': 'Barcode ID is required'
            })
        
        # Check if barcode already exists for another product
        existing_product = Product.objects.filter(
            barcode_id=new_barcode_id,
            user=request.user
        ).exclude(pk=product_id).first()
        
        if existing_product:
            return JsonResponse({
                'success': False,
                'message': f'Barcode already exists for product: {existing_product.product_name}'
            })
        
        # Update the barcode
        product.barcode_id = new_barcode_id
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Barcode updated successfully',
            'barcode_id': new_barcode_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating barcode: {str(e)}'
        })

def generate_unique_product_code(length=8, prefix='PRD'):
    while True:
        random_code = prefix + ''.join(random.choices(string.digits + string.ascii_uppercase, k=length))
        if not Product.objects.filter(product_code=random_code).exists():
            return random_code
@login_required
def product_create(request):
    categories = Product.objects.filter(user=request.user) \
    .exclude(category__isnull=True) \
    .exclude(category__exact='') \
    .values_list('category', flat=True).distinct()
    tax_rates = Product.objects.filter(user=request.user) \
    .exclude(tax_rate__isnull=True).values_list('tax_rate', flat=True).distinct()
    unit_of_measure = Product.objects.filter(
    user=request.user
    ).exclude(
        unit_of_measure__isnull=True
    ).exclude(
        unit_of_measure__exact=''
    ).values_list(
        'unit_of_measure', flat=True
    ).distinct()

    
   
    if request.method == 'POST':
       
            # User
            user = request.user

            # Product Details
            product_name = request.POST.get('itemName', '').strip()
            
            product_code =  generate_unique_product_code()
            description = request.POST.get('description', '').strip()
            discount_raw = request.POST.get('discount', '').strip()
            discount = float(discount_raw.replace('%', '').strip())
            expirydate_raw = request.POST.get('date', '').strip()
            expiry_date = datetime.strptime(expirydate_raw, '%Y-%m-%d').date() if expirydate_raw else None
            purchasess_price=Decimal(request.POST.get('purchasess_price', '0').strip() or '0')

            # Category (new or existing)
            category = request.POST.get('category')
            if category == '__new__':
                category = request.POST.get('categoryInput', '').strip()

            # Tax Rate (new or existing)
            tax_rate = request.POST.get('tax_rate')
            if tax_rate == '__new__':
                tax_rate = request.POST.get('taxRateInput', '0').strip()
            tax_rate = Decimal(tax_rate) if tax_rate else Decimal('0.00')

            # Unit of Measure (new or existing)
            unit_of_measure = request.POST.get('unit_of_measure')
            if unit_of_measure == '__new__':
                unit_of_measure = request.POST.get('unitInput', '').strip()

            # Pricing
            sale_price = Decimal(request.POST.get('sale_price', '0').strip() or '0')
            purchase_price = Decimal(request.POST.get('purchase_price', '0').strip() or '0')

            # Stock
            opening_stock = int(request.POST.get('opening_stock', '0').strip() or '0')
            stock_quantity = opening_stock  # initially same

            # Barcode
            barcode_id = request.POST.get('itemCode', '').strip()
           

            # Save Product
            Product.objects.create(
                product_name=product_name,
                unit_price=sale_price,
                product_code=product_code,
                description=description,
                discount=discount,
                category=category,
                tax_rate=tax_rate,
                unit_of_measure=unit_of_measure,
                sale_price=sale_price,
                mrp=purchase_price,
                opening_stock=opening_stock,
                stock_quantity=stock_quantity,
                barcode_id=barcode_id,
                expiry_date=expiry_date,
                purchase_price=purchasess_price,
                user=user,
            )

            messages.success(request, "✅ Product created successfully!")
            return redirect('product_list')
      
    return render(request, 'products/productform.html', {'action': 'Add','categories':categories,'tax_rates':tax_rates,'unit_of_measure':unit_of_measure})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    unit_of_measure = Product.objects.filter(
    user=request.user
    ).exclude(
        unit_of_measure__isnull=True
    ).exclude(
        unit_of_measure__exact=''
    ).values_list(
        'unit_of_measure', flat=True
    ).distinct()

    if request.method == 'POST':
        try:
            product.product_name = request.POST.get('itemName', '').strip()
            product.description = request.POST.get('description', '').strip()
            discount_raw = request.POST.get('discount', '').strip()
            discount = float(discount_raw.replace('%', '').strip())
            product.discount = discount

            # Category
            category = request.POST.get('category')
            if category == '__new__':
                category = request.POST.get('categoryInput', '').strip()
            product.category = category

            # Tax Rate
            tax_rate = request.POST.get('tax_rate')
            if tax_rate == '__new__':
                tax_rate = request.POST.get('taxRateInput', '0').strip()
            product.tax_rate = Decimal(tax_rate or '0.00')

            # Unit of Measure
            unit = request.POST.get('unit_of_measure')
            if unit == '__new__':
                unit = request.POST.get('unitInput', '').strip()
            product.unit_of_measure = unit

            product.sale_price = Decimal(request.POST.get('sale_price', '0') or '0')
            product.unit_price =Decimal(request.POST.get('sale_price', '0') or '0')
            product.mrp = Decimal(request.POST.get('purchase_price', '0') or '0')
            product.opening_stock = int(request.POST.get('opening_stock', '0') or '0')
            product.stock_quantity = product.opening_stock
            expirydate_raw = request.POST.get('date', '').strip()
            expiry_date = datetime.strptime(expirydate_raw, '%Y-%m-%d').date() if expirydate_raw else None
            product.expiry_date=expiry_date
            product.barcode_id = request.POST.get('barcode_id', '').strip()
            product.purchase_price=Decimal(request.POST.get('purchasess_price', '0') or '0')

            product.save()
            messages.success(request, "✅ Product updated successfully!")
          
            return redirect('product_list')

        except Exception as e:
            messages.error(request, f"❌ Error updating product: {e}")
            return redirect('product_list')
    return render(request, 'products/product_form.html', { 'action': 'Update','product':product,'categories': Product.objects.values_list('category', flat=True).distinct(),
        'tax_rates': Product.objects.values_list('tax_rate', flat=True).distinct(),
        'unit_of_measure': unit_of_measure})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})

@login_required
def party_list(request):
    if not check_user_permission(request.user, 'can_view_parties'):
           return redirect("access_denide")
    access=UserAccess.objects.get(user=request.user)
   
    parties = Party.objects.filter(user=request.user)
    types = Party.objects.filter(user=request.user).values_list('party_type', flat=True).distinct()
    categories = Party.objects.filter(user=request.user).values_list('party_category', flat=True).distinct()
    
    context = {
        'parties': parties,
        'types': types,
        'categories': categories,
        'access':access
    }
    return render(request, 'party/party_list.html', context)

@login_required
def party_create(request):
    if request.method == 'POST':
        form = PartyForm(request.POST)
        if form.is_valid():
            party = form.save(commit=False)
            party.user = request.user
            party.save()
            messages.success(request, 'Party created successfully')
            return redirect('party_list')
    else:
        form = PartyForm()
    return render(request, 'party/party_form.html', {'form': form, 'action': 'Add', 'title': 'Add Party'})

@login_required
def party_update(request, pk):
    party = get_object_or_404(Party, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party updated successfully')
            return redirect('party_list')
    else:
        form = PartyForm(instance=party)
    return render(request, 'party/party_form.html', {'form': form, 'action': 'Edit', 'title': 'Edit Party'})

@login_required
def party_delete(request, pk):
    party = get_object_or_404(Party, pk=pk, user=request.user)
    if request.method == 'POST':
        party.delete()
        messages.success(request, 'Party deleted successfully')
        return redirect('party_list')
    return render(request, 'party/party_confirm_delete.html', {'party': party})

@login_required
def invoice_list(request):
    """List all invoices for the current user with filtering, search, and pagination"""
    invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')
    if not check_user_permission(request.user, 'can_view_sales_invoices'):
           return redirect("access_denide")
    access=UserAccess.objects.get(user=request.user)
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search', '').strip()
    
    # Apply date filtering
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            invoices = invoices.filter(invoice_date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            invoices = invoices.filter(invoice_date__lte=end_date_obj)
        except ValueError:
            pass
    
    # Apply search filtering
    if search_query:
        invoices = invoices.filter(
            Q(invoice_no__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Handle CSV download
    if request.GET.get('download') == 'csv':
        return download_invoices_csv(invoices, start_date, end_date)
    
    # Pagination
    paginator = Paginator(invoices, 10)  # Show 10 invoices per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if invoice settings exist
    setitings_invoice = Sales_invoice_settings.objects.filter(user=request.user).exists()
    
    context = {
        'page_obj': page_obj,
        'invoices': page_obj,  # For template compatibility
        'setitings_invoice': setitings_invoice,
        'start_date': start_date,
        'end_date': end_date,
        'search_query': search_query,
        'total_invoices': invoices.count(),
        'access':access
    }
    
    return render(request, 'invoices/invoice_list.html', context)

def download_invoices_csv(invoices, start_date=None, end_date=None):
    """Download invoices as CSV file"""
    # Create filename based on date range
    if start_date and end_date:
        filename = f'invoices_{start_date}_to_{end_date}.csv'
    elif start_date:
        filename = f'invoices_from_{start_date}.csv'
    elif end_date:
        filename = f'invoices_until_{end_date}.csv'
    else:
        filename = f'all_invoices_{datetime.now().strftime("%Y%m%d")}.csv'
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    writer.writerow([
        'Invoice No',
        'Party Name',
        'Invoice Date',
        'Due Date',
        'Amount',
        'Status',
        'Created At'
    ])
    
    for invoice in invoices:
        writer.writerow([
            invoice.invoice_no,
            invoice.name,
            invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
            invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
            invoice.amount,
            invoice.get_status_display(),
            invoice.created_at.strftime('%Y-%m-%d %H:%M:%S') if invoice.created_at else ''
        ])
    
    return response

@login_required
def invoice_create(request):
    # Preload banks, parties, and products for form
    banks = TotalBalance.objects.filter(user=request.user, payment_type='Bank').values('account_name').distinct()
    parties = Party.objects.filter(user=request.user, status=True)
    products = Product.objects.filter(user=request.user, status=True)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Lock settings row and get invoice number
                settings = Sales_invoice_settings.objects.select_for_update().get(user=request.user)
                invoice_no = f"INV-{settings.last_invoice_number + 1}"

                # 2. Get form data
                party_id = request.POST.get('party')
                party_name = request.POST.get('party_name')
                party_phone = request.POST.get('party_phone') or "0987654321"
                invoice_date = request.POST.get('invoice_date')
                due_date = request.POST.get('due_date')
                payment_mode = request.POST.get('payment_mode')
                bank = request.POST.get('bank_name')
                invoice_status = request.POST.get('is_full_paid')

                total_amount = Decimal(request.POST.get('manual_total_amount') or '0')
                amount_paid = Decimal(request.POST.get('amount_paid') or '0')

                # 3. Determine payment status
                if invoice_status == 'on' or amount_paid >= total_amount:
                    status = 'paid'
                    amount_paid = total_amount
                    remaining_amount = Decimal('0.00')
                elif amount_paid > 0:
                    status = 'partial'
                    remaining_amount = total_amount - amount_paid
                else:
                    status = 'unpaid'
                    remaining_amount = total_amount

                # 4. Handle party (new or existing)
                if party_id:
                    party = get_object_or_404(Party, id=party_id, user=request.user)
                    selected_party_name = party.party_name
                    selected_party_num = party_id
                else:
                    selected_party_name = party_name
                    selected_party_num = party_phone
                    party_exists = Party.objects.filter(user=request.user, party_name=selected_party_name).first()

                    if not party_exists:
                        Party.objects.create(
                            user=request.user,
                            party_name=selected_party_name,
                            party_contact=selected_party_num
                        )

                # 5. Load and validate items
                items_data = request.POST.get('items_data')
                parsed_data = json.loads(items_data) if items_data else {}
                items = parsed_data.get('items', [])

                if not isinstance(items, list) or not items:
                    messages.error(request, 'Please add at least one item.')
                    return redirect('invoice_create')

                # 6. Create invoice
                invoice = Invoice.objects.create(
                    user=request.user,
                    name=selected_party_name,
                    number=selected_party_num,
                    invoice_no=invoice_no,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    status=status,
                    payment_mode=payment_mode,
                    bank=bank,
                    amount=total_amount,
                    amount_paid=amount_paid,
                    remaining_amount=remaining_amount,
                )

                # 7. Handle bank balance update if any amount paid
                if bank and amount_paid > 0:
                    try:
                        money = TotalBalance.objects.get(user=request.user, payment_type='Bank', account_name=bank)
                    except TotalBalance.MultipleObjectsReturned:
                        money = TotalBalance.objects.filter(user=request.user, payment_type='Bank', account_name=bank).first()
                    except TotalBalance.DoesNotExist:
                        money = TotalBalance.objects.create(user=request.user, payment_type='Bank', account_name=bank, amount=0)

                    money.amount += amount_paid
                    money.save()

                # 8. Create invoice items and update stock
                for item in items:
                    product = get_object_or_404(Product, id=item['product_id'], user=request.user)

                    if product.stock_quantity < item['quantity']:
                        messages.error(request, f'Not enough stock for {product.product_name}')
                        raise Exception(f'Insufficient stock for {product.product_name}')

                    product.stock_quantity -= item['quantity']
                    product.save()

                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=item['product_id'],
                        product_name=item['product_name'],
                        product_description=item.get('description', ''),
                        quantity=item['quantity'],
                        rate=Decimal(str(item['rate'])),
                        tax=Decimal(str(item.get('tax_rate', 0))),
                        discount=item.get('discount_rate', ''),
                        amount=Decimal(str(item['amount']))
                    )

                # 9. Increment invoice number AFTER success
                settings.last_invoice_number += 1
                settings.save(update_fields=['last_invoice_number'])

                messages.success(request, f'Invoice {invoice_no} created successfully!')
                return redirect('invoice_detail', pk=invoice.pk)

        except Exception as e:
            messages.error(request, f'Error creating invoice: {str(e)}')

    # For GET request — safely fetch next invoice preview for display only
    try:
        settings = Sales_invoice_settings.objects.get(user=request.user)
        next_invoice_no = f"INV-{settings.last_invoice_number + 1}"
    except Sales_invoice_settings.DoesNotExist:
        next_invoice_no = "INV-7035"

    context = {
        'parties': parties,
        'products': products,
        'next_invoice_no': next_invoice_no,
        'banks': banks,
    }
    return render(request, 'invoices/invoice_create.html', context)
@login_required
@csrf_exempt
def scan_barcode(request):
    """Handle barcode scanning and return product details"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            barcode = data.get('barcode', '').strip()
            
            if not barcode:
                return JsonResponse({
                    'success': False,
                    'message': 'Barcode is required'
                })
            
            # Search for product by barcode_id
            try:
                product = Product.objects.get(
                    barcode_id=barcode,
                    user=request.user,
                    status=True
                )
                
                return JsonResponse({
                    'success': True,
                    'product': {
                        'id': product.id,
                        'product_name': product.product_name,
                        'product_code': product.product_code,
                        'description': product.description,
                        'unit_price': float(product.unit_price),
                        'sale_price': float(product.sale_price),
                        'stock_quantity': product.stock_quantity,
                        'category': product.category,
                        'tax_rate': float(product.tax_rate),
                        'barcode_id': product.barcode_id,
                        'unit_of_measure': product.unit_of_measure
                    }
                })
                
            except Product.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Product with barcode "{barcode}" not found in your inventory'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing barcode: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Only POST method allowed'
    })

@login_required
def get_products_ajax(request):
    """Get products for AJAX requests"""
    products = Product.objects.filter(user=request.user, status=True)
    
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'product_name': product.product_name,
            'product_code': product.product_code,
            'description': product.description,
            'unit_price': float(product.unit_price),
            'sale_price': float(product.sale_price),
            'stock_quantity': product.stock_quantity,
            'category': product.category,
            'tax_rate': float(product.tax_rate),
            'barcode_id': product.barcode_id,
            'unit_of_measure': product.unit_of_measure
        })
    
    return JsonResponse(products_data, safe=False)

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    invoice_setting = get_object_or_404(Sales_invoice_settings, user=request.user)
    items = invoice.items.all()

    enriched_items = []
    subtotal = Decimal('0.00')
    total_tax = Decimal('0.00')
    total_discount = Decimal('0.00')

    for item in items:
        tax_rate = item.tax or Decimal('0.00')
        unit = ''
        discount_value = Decimal('0.00')

        # Optional: Fetch unit from Product
        try:
            product = Product.objects.get(id=item.product_id)
            unit = product.unit_of_measure
        except Product.DoesNotExist:
            pass

        # Parse discount string
        discount_raw = item.discount or ''
        try:
            if discount_raw.endswith('%'):
                percent = Decimal(discount_raw.strip('%'))
                discount_value = item.amount * (percent / Decimal('100'))
            elif discount_raw.startswith('₹'):
                discount_value = Decimal(discount_raw.strip('₹'))
            else:
                discount_value = Decimal(discount_raw)
        except Exception:
            discount_value = Decimal('0.00')

        # Tax on discounted amount
        taxable_amount = item.amount - discount_value
        tax_amount = taxable_amount * (tax_rate / Decimal('100'))

        # Totals
        subtotal += item.amount
        total_discount += discount_value
        total_tax += tax_amount


        enriched_items.append({
            'item': item,
            'unit': unit,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'discount': discount_value,
            'net_amount': taxable_amount + tax_amount,
        })

    # Calculate total
    calculated_total = subtotal - total_discount + total_tax
    final_total = invoice.amount
    extra_amount = final_total - calculated_total  # ✅ can be positive or negative
    valid_items = [i for i in enriched_items if i['item'].quantity > 0]

    context = {
        'invoice': invoice,
        'invoice_setting': invoice_setting,
        'items': valid_items ,
        'subtotal': subtotal,
        'total_discount': total_discount,
        'total_tax': total_tax,
        'calculated_total': calculated_total,
        'final_total': final_total,
        'extra_amount': extra_amount,  # ✅ show +ve or -ve as per condition
        'paid_amount': invoice.amount_paid,
        'balance': invoice.remaining_amount,
        'status': invoice.status,
    }

    return render(request, 'invoices/invoice_detail.html', context)
@login_required
def return_invoice_detail(request, pk):
    if not check_user_permission(request.user, 'can_view_return_invoices'):
           return redirect("access_denide")


    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    invoice_setting = get_object_or_404(Sales_invoice_settings, user=request.user)
    items = invoice.items.all()

    enriched_items = []
    subtotal = Decimal('0.00')
    total_tax = Decimal('0.00')

    for item in items:
        tax_rate = Decimal('0.00')
        unit = ''

        try:
            product = Product.objects.get(id=item.product_id)
            tax_rate = product.tax_rate
            unit = product.unit_of_measure
        except Product.DoesNotExist:
            pass

        tax_amount = item.amount * (tax_rate / Decimal('100.00'))
        subtotal += item.amount
        total_tax += tax_amount

        enriched_items.append({
            'item': item,
            'tax_amount': tax_amount,
            'tax_rate': tax_rate,
            'unit': unit,
        })

    calculated_total = subtotal + total_tax
    final_total = max(invoice.amount, calculated_total)
    extra_amount = final_total - calculated_total

    context = {
        'invoice': invoice,
        'invoice_setting': invoice_setting,
        'items': enriched_items,
        'subtotal': subtotal,
        'total_tax': total_tax,
        'calculated_total': calculated_total,
        'final_total': final_total,
        'extra_amount': extra_amount,
        'paid_amount': invoice.amount_paid,
        'balance': invoice.remaining_amount,
        'status': invoice.status,
    }
    return render(request, 'invoices/return_invoice_detail.html', context)

@login_required
def invoicesetting(request):
    # Check if user already has a settings record
    setitings_invoice=Sales_invoice_settings.objects.filter(user=request.user).exists()
    if Sales_invoice_settings.objects.filter(user=request.user).exists():

        messages.warning(request, "You have already submitted your invoice settings.")
        return redirect('dashboard')  # Change to your dashboard or appropriate page

    if request.method == 'POST':
        instance = Sales_invoice_settings(
            user=request.user,
            business_name=request.POST.get('business_name'),
            address=request.POST.get('address'),
            gstin=request.POST.get('gstin'),
            mobile=request.POST.get('mobile'),
            email=request.POST.get('email'),
            upi_id=request.POST.get('upi_id'),
            terms1=request.POST.get('terms1'),
            terms2=request.POST.get('terms2'),
            terms3=request.POST.get('terms3'),
            acc_bank_name=request.POST.get('acc_branch_name'),
            ifsc_code=request.POST.get('ifsc_code'),
            account_no=request.POST.get('account_no'),
            upload_sign=request.FILES.get('upload_sign'),
            invoice_number=request.POST.get('invoice')
        )
        instance.save()
        messages.success(request, "Invoice settings saved successfully.")
        return redirect('/invoices')  # Change accordingly

    return render(request, 'invoices/create_invoice_setting.html')

@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    # Store original items for restoring stock
    original_items = list(invoice.items.all().values('product_id', 'quantity'))

    # Store original payment details
    original_payment_mode = invoice.payment_mode
    original_bank = invoice.bank
    original_amount = invoice.amount
    original_status = invoice.status

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Restore stock from original items
                for item in original_items:
                    product = get_object_or_404(Product, id=item['product_id'], user=request.user)
                    product.stock_quantity += item['quantity']
                    product.save()

                # Update invoice fields
                invoice.invoice_date = request.POST.get('invoice_date')
                invoice.due_date = request.POST.get('due_date')
                invoice_status = request.POST.get('is_full_paid')
                manual_total = request.POST.get('manual_total_amount')
                total_amount = Decimal('0.00')
                if manual_total:
                    try:
                        total_amount = Decimal(str(manual_total))
                    except:
                        total_amount = Decimal('0.00')
                if invoice_status == 'on':  # checkbox is checked
                    status = "paid"
                else:
                    status = "unpaid"
                invoice.status = status
                invoice.payment_mode = request.POST.get('payment_mode', '')

                # Handle bank logic
                new_bank = request.POST.get('bank_name') if invoice.payment_mode != 'Cash' else ''
                invoice.bank = new_bank

                invoice.amount = total_amount  # Will be overwritten if manual_total is blank

                # Delete old items
                invoice.items.all().delete()

                # Process updated items
                items_data = request.POST.get('items_data')
                if items_data:
                    items = json.loads(items_data)
                    total_amount = Decimal('0.00')
                    for item in items:
                        product = get_object_or_404(Product, id=item['product_id'], user=request.user)
                        if product.stock_quantity < item['quantity']:
                            raise Exception(f"Not enough stock for {product.product_name}. Available: {product.stock_quantity}")

                        product.stock_quantity -= item['quantity']
                        product.save()

                        InvoiceItem.objects.create(
                            invoice=invoice,
                            product_id=item['product_id'],
                            product_name=item['product_name'],
                            product_description=item.get('description', ''),
                            quantity=item['quantity'],
                            rate=Decimal(str(item['rate'])),
                            amount=Decimal(str(item['amount']))
                        )

                        total_amount += Decimal(str(item['amount']))

                    if not manual_total:
                        invoice.amount = total_amount

                # 🔁 Adjust bank balance only if status changed
                if original_status != status:
                    # Status changed from paid to unpaid → subtract original amount from original bank
                    if original_bank and original_status == "paid" and status == "unpaid":
                        try:
                            bank_entry = TotalBalance.objects.get(
                                user=request.user,
                                account_name=original_bank,
                                payment_type='Bank'
                            )
                            bank_entry.amount -= original_amount
                            bank_entry.save()
                        except TotalBalance.DoesNotExist:
                            raise Exception(f"Bank '{original_bank}' not found for deduction.")

                    # Status changed from unpaid to paid → add amount to selected bank
                    elif status == "paid" and invoice.bank:
                        try:
                            bank_entry = TotalBalance.objects.get(
                                user=request.user,
                                account_name=invoice.bank,
                                payment_type='Bank'
                            )
                            if original_status == "unpaid" and total_amount == original_amount:
                                bank_entry.amount += total_amount
                            elif total_amount != original_amount:
                                diff = total_amount - original_amount
                                bank_entry.amount += diff
                            bank_entry.save()
                        except TotalBalance.DoesNotExist:
                            raise Exception(f"Bank '{invoice.bank}' not found for credit.")

                # Final save
                invoice.save()
                messages.success(request, f"Invoice #{invoice.invoice_no} updated successfully!")
                return redirect('invoice_detail', pk=invoice.pk)

        except Exception as e:
            messages.error(request, f"Error updating invoice: {str(e)}")

    # Data for form
    parties = Party.objects.filter(user=request.user, status=True).order_by('party_name')
    products = Product.objects.filter(user=request.user, status=True).order_by('product_name')
    banks = TotalBalance.objects.filter(user=request.user, payment_type='Bank').order_by('account_name')

    return render(request, 'invoices/invoice_update.html', {
        'invoice': invoice,
        'parties': parties,
        'products': products,
        'banks': banks
    })

@login_required
def invoicesettingedit(request):
    if not check_user_permission(request.user, 'can_edit_profile'):
           return redirect("access_denide")

    invoice_setting = get_object_or_404(Sales_invoice_settings,user=request.user)
    if request.method == 'POST':
        invoice_setting.business_name = request.POST.get('business_name')
        invoice_setting.address = request.POST.get('address')
        invoice_setting.gstin = request.POST.get('gstin')
        invoice_setting.mobile = request.POST.get('mobile')
        invoice_setting.email = request.POST.get('email')
        invoice_setting.upi_id = request.POST.get('upi_id')
        invoice_setting.terms1 = request.POST.get('terms1')
        invoice_setting.terms2 = request.POST.get('terms2')
        invoice_setting.terms3 = request.POST.get('terms3')
        invoice_setting.acc_bank_name = request.POST.get('acc_branch_name')
        invoice_setting.ifsc_code = request.POST.get('ifsc_code')
        invoice_setting.account_no = request.POST.get('account_no')
        invoice_setting.last_invoice_number=request.POST.get('invoice')

        if 'qrcode' in request.FILES:
            invoice_setting.qrcode = request.FILES['qrcode']
        if 'upload_sign' in request.FILES:
            invoice_setting.upload_sign = request.FILES['upload_sign']

        invoice_setting.save()
        return redirect('/invoices')  # Redirect to same or another page
    return render(request,'invoices/edit_invoice_setting.html',{'invoice_setting':invoice_setting})
@login_required
def invoice_delete(request, pk):
    """Delete invoice"""

    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for item in invoice.items.all():
                    product = Product.objects.get(id=item.product_id, user=request.user)
                    product.stock_quantity += item.quantity
                    product.save()
                if invoice.payment_mode in ['UPI', 'Card', 'NetBanking', 'Bank Transfer', 'Cheque']:
                    try:
                        balance = get_object_or_404(
                            TotalBalance,
                            user=request.user,
                            payment_type='Bank',
                            account_name=invoice.bank if invoice.payment_mode in ['UPI', 'Card', 'NetBanking', 'Bank Transfer', 'Cheque'] else None
                        )
          

                        balance.amount -= Decimal(str(invoice.amount))

                        # Prevent negative balance (optional)
                        if balance.amount < 0:
                            balance.amount = Decimal('0.00')

                        balance.save()
                    except Exception as e:
                         messages.error(request, f'Failed to update balance: {e}')
                invoice.delete()
                messages.success(request, 'Invoice deleted and stock restored successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting invoice: {e}')
        
        return redirect('invoice_list')
    
    return render(request, 'invoices/invoice_delete.html', {'invoice': invoice})

@login_required
def get_products_ajax(request):
    """AJAX endpoint to get products with their details"""
    products = Product.objects.filter(user=request.user, status=True).values(
        'id',
        'product_name',
        'product_code',
        'description',
        'category',
        'unit_price',
        'stock_quantity',
        'tax_rate',
        'unit_of_measure',
    )
    return JsonResponse(list(products), safe=False)

@login_required
def get_party_details_ajax(request, party_id):
    """AJAX endpoint to get party details"""
    try:
        party = Party.objects.get(id=party_id, user=request.user)
        data = {
            'id': party.id,
            'name': party.party_name,
            'email': party.party_email,
            'address': party.party_address,
            'contact': party.party_contact,
            'gst': party.party_gst,
        }
        return JsonResponse(data)
    except Party.DoesNotExist:
        return JsonResponse({'error': 'Party not found'}, status=404)
    
@login_required
def payments(request):
    if not check_user_permission(request.user, 'can_view_payment_in'):
           return redirect("access_denide")
    access=UserAccess.objects.get(user=request.user)
    
    payment=Payment.objects.filter(user=request.user).order_by('-created_at')
    context={'payment':payment,
             'access':access
             
        }
    return render(request,'Payments/payment.html',context)

@login_required 
def payment2_partial(request): 
    party = Party.objects.filter(user=request.user)
    banks = TotalBalance.objects.filter(user=request.user, payment_type='Bank')
    
    if request.method == "POST": 
        party_name = request.POST.get("party") 
        phone = request.POST.get("phone") 
        amount = request.POST.get("amount") 
        payment_date = request.POST.get("date") 
        payment_mode = request.POST.get("mode") 
        notes = request.POST.get("notes")
        bank_id = request.POST.get("bank")
        
        try:
            with transaction.atomic():
                # Get the selected bank if payment mode is not Cash
                selected_bank = None
                if payment_mode != 'Cash' and bank_id:
                    selected_bank = get_object_or_404(TotalBalance, id=bank_id, user=request.user)
                    
                    # Check if bank has sufficient balance
                    if selected_bank.amount < Decimal(amount):
                        messages.error(request, f"Insufficient balance in {selected_bank.account_name}. Available: ₹{selected_bank.amount}")
                        context = {'party': party, 'banks': banks}
                        return render(request, "Payments/payment2.html", context)
                    
                    # Add amount from bank
                    selected_bank.amount += Decimal(amount)
                    selected_bank.save()
                
                # Create payment record
                Payment.objects.create( 
                    user=request.user, 
                    party_name=party_name, 
                    party_phone=phone, 
                    amount=amount, 
                    date=payment_date, 
                    payment_mode=payment_mode, 
                    selected_bank=selected_bank,
                    notes=notes, 
                )
                
                messages.success(request, "Payment successfully recorded.") 
                return redirect("payments")
                
        except Exception as e:
            messages.error(request, f"Error recording payment: {str(e)}")
    
    context = {
        'party': party,
        'banks': banks,
    } 
    
    return render(request, "Payments/payment2.html", context)

@login_required
def payedit(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    party = Party.objects.filter(user=request.user)

    if request.method == "POST":
        payment.party_name = request.POST.get("party")
        payment.party_phone = request.POST.get("phone")
        payment.amount = request.POST.get("amount")
        payment.date = request.POST.get("date")
        payment.payment_mode = request.POST.get("mode")
        payment.notes = request.POST.get("notes")
        payment.save()

        messages.success(request, "Payment successfully updated.")
        return redirect("payments")

    context = {
        'payment': payment,
        'party': party,
        'action': 'Edit',
        'title': 'Edit Payment'
    }
    return render(request, "Payments/payment2.html", context)

def paydelete(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                # If payment was made from a bank account, add the amount back
                if payment.selected_bank and payment.payment_mode != 'Cash':
                    payment.selected_bank.amount -= payment.amount
                    payment.selected_bank.save()
                
                payment.delete()
                messages.success(request, "Payment deleted successfully and amount restored to bank account.")
                return redirect("payments")
                
        except Exception as e:
            messages.error(request, f"Error deleting payment: {str(e)}")
            return redirect("payments")

    # Optional: If accessed via GET, confirm first (safer)
    return render(request, "Payments/payment_confirm_delete.html", {"payment": payment})

@login_required
def cashbank(request):
    if not check_user_permission(request.user, 'can_view_cash_and_bank'):
           return redirect("access_denide")
    access=UserAccess.objects.get(user=request.user)
    transactions = TotalBalance.objects.filter(user=request.user).order_by('-date')
    total_balance = TotalBalance.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    cash_in_hand = TotalBalance.objects.filter(user=request.user,payment_type='Cash').aggregate(total=Sum('amount'))['total'] or 0
    cash_in_bank = TotalBalance.objects.filter(user=request.user,payment_type='Bank').aggregate(total=Sum('amount'))['total'] or 0
    accounts = TotalBalance.objects.filter(
        user=request.user
    ).filter(
        ~Q(account_name__isnull=True),     # exclude None
        ~Q(account_name=''),               # exclude empty string
        ~Q(account_name='0') ,              # optionally exclude '0'
        ~Q(account_name=None) ,              # optionally exclude '0'
    ).values_list('account_name', flat=True).distinct()

    user=request.user
    if request.method=='POST':
        payment_type = request.POST.get('payment_type')
        account_name = request.POST.get('account_name', '')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        remarks = request.POST.get('remarks', 'Opening Balance')

        obj=TotalBalance.objects.create(user=user,payment_type=payment_type,account_name=account_name,amount=amount,date=date,remarks=remarks)
        return redirect('/cashbank')

    context={'transactions':transactions,
             'total_balance':total_balance,
             'cash_in_hand':cash_in_hand,
             'cash_in_bank':cash_in_bank,
             'accounts':accounts,
             'access':access
            
             }



    return render(request,'Bank/cashandbank.html',context)
@login_required
def cashedit(request,pk):
    transactions = TotalBalance.objects.filter(user=request.user).order_by('-date')
    total_balance = TotalBalance.objects.aggregate(total=Sum('amount'))['total'] or 0
    cash_in_hand = TotalBalance.objects.filter(user=request.user,payment_type='Cash').aggregate(total=Sum('amount'))['total'] or 0
    cash_in_bank = TotalBalance.objects.filter(user=request.user,payment_type='Bank').aggregate(total=Sum('amount'))['total'] or 0
    transactionedit = get_object_or_404(TotalBalance, pk=pk, user=request.user)
    trans = TotalBalance.objects.filter(user=request.user)
    user=request.user
    if request.method=='POST':
        transactionedit.account_name=request.POST['account_name']
        transactionedit.payment_type=request.POST['payment_type']
        transactionedit.amount=request.POST['amount']
        transactionedit.date=request.POST['date']
        transactionedit.remarks=request.POST['remarks']
        transactionedit.save()
        return redirect('/cashbank')

    context={'transactions':transactions,
             'total_balance':total_balance,
             'cash_in_hand':cash_in_hand,
             'cash_in_bank':cash_in_bank
             }
    return render(request,'Bank/cashandbank.html',context)
@login_required
def cashdelete(request,pk):

    transaction = get_object_or_404(TotalBalance, pk=pk, user=request.user)
    
    if request.method == "POST":
        transaction.delete()
        messages.success(request, "transaction deleted successfully.")
        return redirect("/cashbank")  # Replace with your payment list view name

    # Optional: If accessed via GET, confirm first (safer)
    return render(request, "Bank/cashbank_confirm_delete.html",{'transaction':transaction})

def logout_view(request):
    logout(request)
    return redirect('/')
@csrf_exempt  # only if you're not using CSRF token in the header
def set_invoice_paid(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            invoice_id = data.get("invoice_id")
            is_paid = data.get("is_paid", False)
            invoice = Invoice.objects.get(id=invoice_id)
            invoice.status = "paid" if is_paid else "unpaid"
            invoice.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid method"})


@login_required
def return_invoice_view(request):
    """Main return invoice view"""
    if request.method == 'POST':
        form = ReturnInvoiceForm(request.POST)
        if form.is_valid():
            invoice_id = form.cleaned_data['invoice_id']
            try:
                invoice = Invoice.objects.get(invoice_no=invoice_id, user=request.user)
                # Check if invoice is eligible for return
                if invoice.status == 'return':
                    messages.error(request, 'This invoice has already been refunded.')
                    return render(request, 'return_invoice.html', {'form': form})
                
                invoice_items = invoice.items.all()
                return render(request, 'return_invoice.html', {
                    'form': form,
                    'invoice': invoice,
                    'invoice_items': invoice_items
                })
            except Invoice.DoesNotExist:
                messages.error(request, 'Invoice not found or you do not have permission to access it.')
    else:
        form = ReturnInvoiceForm()
    
    return render(request, 'return_invoice.html', {'form': form})

@login_required
@csrf_exempt
def process_return(request):
    """Process the return invoice"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_id = data.get('invoice_id')
            selected_items = data.get('selected_items', [])
            
            if not invoice_id or not selected_items:
                return JsonResponse({'success': False, 'message': 'Missing required data'})
            
            # Get original invoice
            original_invoice = get_object_or_404(Invoice, invoice_no=invoice_id, user=request.user)
            
            # Process return in transaction
            with transaction.atomic():
                return_invoice = create_return_invoice(original_invoice, selected_items, request.user)
                update_inventory(selected_items, request.user)
                update_balance(return_invoice.amount, request.user)
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Return processed successfully',
                    'return_invoice_id': return_invoice.invoice_no
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta

def create_return_invoice(original_invoice, selected_items, user):
    """Create a return invoice and deduct from original invoice"""

    return_invoice_no = f"RET-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    invoice_date = timezone.now().date()
    total_return_amount = Decimal('0.00')

    return_invoice = Invoice.objects.create(
        user=user,
        name=original_invoice.name,
        number=original_invoice.number,
        invoice_no=return_invoice_no,
        invoice_date=invoice_date,
        due_date=invoice_date + relativedelta(months=1),
        amount=0,
        amount_paid=0,
        remaining_amount=0,
        status='return',
        payment_mode=original_invoice.payment_mode,
        bank=original_invoice.bank
    )

    for item_data in selected_items:
        original_item = get_object_or_404(InvoiceItem, id=item_data['item_id'])
        return_quantity = int(item_data['quantity'])

        if return_quantity > original_item.quantity:
            raise ValueError(f"Return quantity exceeds original quantity for {original_item.product_name}")

        # Deduct quantity from original item
        original_item.quantity -= return_quantity
        original_item.save()  # amount auto-updates in model

        # Get tax
        try:
            product = Product.objects.get(id=original_item.product_id, user=user)
            tax_rate = product.tax_rate
        except Product.DoesNotExist:
            tax_rate = Decimal('0.00')

        base_amount = original_item.rate * return_quantity
        tax_amount = base_amount * (tax_rate / 100)
        total_item_amount = base_amount + tax_amount

        # Create return item
        InvoiceItem.objects.create(
            invoice=return_invoice,
            product_id=original_item.product_id,
            product_name=original_item.product_name,
            product_description=original_item.product_description,
            quantity=return_quantity,
            rate=original_item.rate,
            amount=total_item_amount,
            discount=original_item.discount
        )

        total_return_amount += total_item_amount

    # Set return invoice total
    return_invoice.amount = total_return_amount
    return_invoice.save()

    # Deduct return from original invoice's amount and remaining
    original_invoice.amount = max(original_invoice.amount - total_return_amount, Decimal('0.00'))
    original_invoice.amount_paid = max(original_invoice.amount_paid - total_return_amount, Decimal('0.00'))
    original_invoice.remaining_amount = max(original_invoice.amount - original_invoice.amount_paid, Decimal('0.00'))
    original_invoice.save()

    return return_invoice



def update_inventory(selected_items, user):
    """Update product inventory for returned items"""
    for item_data in selected_items:
        original_item = get_object_or_404(InvoiceItem, id=item_data['item_id'])
        return_quantity = int(item_data['quantity'])
        
        try:
            product = Product.objects.get(id=original_item.product_id, user=user)
            product.stock_quantity += return_quantity
            product.save()
        except Product.DoesNotExist:
            # Log this but don't fail the transaction
            pass

def update_balance(return_amount, user):
    """Update total balance by deducting return amount"""
    # Get the most recent balance entry for the user
    latest_balance = TotalBalance.objects.filter(user=user).order_by('-created_at').first()
    
    if latest_balance:
        # Create a new balance entry with deducted amount
        TotalBalance.objects.create(
            user=user,
            account_name=latest_balance.account_name,
            amount=-return_amount,  # Negative amount for return
            date=timezone.now().date(),
            remarks="Return Invoice Deduction",
            payment_type=latest_balance.payment_type
        )
    else:
        # If no balance exists, create one with negative amount
        TotalBalance.objects.create(
            user=user,
            account_name="Default Account",
            amount=-return_amount,
            date=timezone.now().date(),
            remarks="Return Invoice Deduction",
            payment_type="Cash"
        )

@login_required
def access_denide(request):
    return render(request, "access_denide.html") 

@login_required

def sales_invoice(request):
    banks = TotalBalance.objects.filter(user=request.user, payment_type='Bank').values('account_name').distinct()
    parties = Party.objects.filter(user=request.user, status=True)
    products = Product.objects.filter(user=request.user, status=True)  # Keep for item dropdown

    if request.method == 'POST':
        try:
            with transaction.atomic():
                settings = Sales_invoice_settings.objects.select_for_update().get(user=request.user)
                invoice_no = f"INV-{settings.last_invoice_number + 1}"

                party_id = request.POST.get('party')
                party_name = request.POST.get('party_name')
                party_phone = request.POST.get('party_phone') or "0987654321"
                invoice_date = request.POST.get('invoice_date')
                due_date = request.POST.get('due_date')
                payment_mode = request.POST.get('payment_mode')
                bank = request.POST.get('bank_name')
                invoice_status = request.POST.get('is_full_paid')

                total_amount = Decimal(request.POST.get('manual_total_amount') or '0')
                amount_paid = Decimal(request.POST.get('amount_paid') or '0')

                # Payment status logic
                if invoice_status == 'on' or amount_paid >= total_amount:
                    status = 'paid'
                    amount_paid = total_amount
                    remaining_amount = Decimal('0.00')
                elif amount_paid > 0:
                    status = 'partial'
                    remaining_amount = total_amount - amount_paid
                else:
                    status = 'unpaid'
                    remaining_amount = total_amount

                # Handle party (new or existing)
                if party_id:
                    party = get_object_or_404(Party, id=party_id, user=request.user)
                    selected_party_name = party.party_name
                    selected_party_num = party_id
                else:
                    selected_party_name = party_name
                    selected_party_num = party_phone
                    party_exists = Party.objects.filter(user=request.user, party_name=selected_party_name).first()

                    if not party_exists:
                        Party.objects.create(
                            user=request.user,
                            party_name=selected_party_name,
                            party_contact=selected_party_num
                        )

                # Load and validate items
                items_data = request.POST.get('items_data')
                parsed_data = json.loads(items_data) if items_data else {}
                items = parsed_data.get('items', [])

                if not isinstance(items, list) or not items:
                    messages.error(request, 'Please add at least one item.')
                    return redirect('invoice_create')

                # Create invoice
                invoice = Invoice.objects.create(
                    user=request.user,
                    name=selected_party_name,
                    number=selected_party_num,
                    invoice_no=invoice_no,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    status=status,
                    payment_mode=payment_mode,
                    bank=bank,
                    amount=total_amount,
                    amount_paid=amount_paid,
                    remaining_amount=remaining_amount,
                )

                # Update bank balance
                if bank and amount_paid > 0:
                    try:
                        money = TotalBalance.objects.get(user=request.user, payment_type='Bank', account_name=bank)
                    except TotalBalance.MultipleObjectsReturned:
                        money = TotalBalance.objects.filter(user=request.user, payment_type='Bank', account_name=bank).first()
                    except TotalBalance.DoesNotExist:
                        money = TotalBalance.objects.create(user=request.user, payment_type='Bank', account_name=bank, amount=0)

                    money.amount += amount_paid
                    money.save()

                # Create invoice items and update stock
                for item in items:
                    product = get_object_or_404(Product, id=item['product_id'], user=request.user)

                    if product.stock_quantity < item['quantity']:
                        messages.error(request, f'Not enough stock for {product.product_name}')
                        raise Exception(f'Insufficient stock for {product.product_name}')

                    product.stock_quantity -= item['quantity']
                    product.save()

                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=item['product_id'],
                        product_name="",
                        product_description="",
                        quantity=item['quantity'],
                        rate=Decimal(str(item['rate'])),
                        tax=Decimal(str(item.get('tax_rate', 0))),
                        discount=item.get('discount_rate', ''),
                        amount=Decimal(str(item['amount']))
                    )
                # Increment invoice number after all success
                settings.last_invoice_number += 1
                settings.save(update_fields=['last_invoice_number'])

                messages.success(request, f'Invoice {invoice_no} created successfully!')
                return redirect('invoice_detail', pk=invoice.pk)

        except Exception as e:
            messages.error(request, f'Error creating invoice: {str(e)}')

    # For GET request
    try:
        settings = Sales_invoice_settings.objects.get(user=request.user)
        next_invoice_no = f"INV-{settings.last_invoice_number + 1}"
    except Sales_invoice_settings.DoesNotExist:
        next_invoice_no = "INV-7035"

    context = {
        'parties': parties,
        'products': products,
        'next_invoice_no': next_invoice_no,
        'banks': banks,
    }
    return render(request, "invoices/salesinvoice.html", context)