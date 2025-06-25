from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Party, Product, Invoice, InvoiceItem, Payment, TotalBalance,Sales_invoice_settings
from .serializers import PartySerializer, ProductSerializer, InvoiceSerializer, InvoiceListSerializer, InvoiceItemSerializer, PaymentSerializer
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from rest_framework.permissions import AllowAny
import random
import string
from django.template.loader import render_to_string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from .forms import ProductForm, PartyForm
import uuid
from django.http import JsonResponse
from decimal import Decimal
from django.db import transaction

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
def product_list(request):
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

@api_view(['PUT'])
@permission_classes([AllowAny])
def product_update(request, product_id):
    """Update product details"""
    try:
        product = Product.objects.get(id=product_id)
        data = request.data.copy()
        
        # Handle user field
        if 'user_id' in data:
            data['user'] = data.pop('user_id')
            
        serializer = ProductSerializer(product, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
def invoice_list(request):
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
def invoice_detail(request, invoice_id):
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
def invoice_update(request, invoice_id):
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
def invoice_delete(request, invoice_id):
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

@login_required
def dashboard(request):
    user = request.user

    # To Collect: Sum of all invoice amounts
    to_collect = Invoice.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0

    # To Pay: Sum of all payment amounts
    to_pay = Payment.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0

    # Stock Value: quantity * unit_price
    stock_value = Product.objects.filter(user=user).aggregate(
        total=Sum(F('stock_quantity') * F('unit_price'))
    )['total'] or 0

    # Total Balance: sum of TotalBalance
    total_balance = TotalBalance.objects.aggregate(total=Sum('amount'))['total'] or 0

    invoices = Invoice.objects.filter(user=user)
    payments = Payment.objects.filter(user=user)

    return render(request, 'dashboard.html', {
        'to_collect': to_collect,
        'to_pay': to_pay,
        'stock_value': stock_value,
        'total_balance': total_balance,
        'invoices': invoices,
        'payments': payments
    })

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
    products = Product.objects.filter(user=request.user)
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category=category_filter)
    categories = Product.objects.filter(user=request.user).values_list('category', flat=True).distinct()
    
    context = {
        'products': products,
        'category_filter': category_filter,
        'categories': categories,
    }
    
    return render(request, 'products/product_list.html', context)

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
            hsn_code = request.POST.get('hsn_code', '').strip()

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
                hsn_code=hsn_code,
                category=category,
                tax_rate=tax_rate,
                unit_of_measure=unit_of_measure,
                sale_price=sale_price,
                purchase_price=purchase_price,
                opening_stock=opening_stock,
                stock_quantity=stock_quantity,
                barcode_id=barcode_id,
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
            product.hsn_code = request.POST.get('hsn_code', '').strip()

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
            product.purchase_price = Decimal(request.POST.get('purchase_price', '0') or '0')
            product.opening_stock = int(request.POST.get('opening_stock', '0') or '0')
            product.stock_quantity = product.opening_stock
            product.barcode_id = request.POST.get('barcode_id', '').strip()

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
    parties = Party.objects.filter(user=request.user)
    types = Party.objects.filter(user=request.user).values_list('party_type', flat=True).distinct()
    categories = Party.objects.filter(user=request.user).values_list('party_category', flat=True).distinct()
    
    context = {
        'parties': parties,
        'types': types,
        'categories': categories,
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
    """List all invoices for the current user"""
    invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')
    setitings_invoice=Sales_invoice_settings.objects.filter(user=request.user).exists()
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices,'setitings_invoice':setitings_invoice})

@login_required
def invoice_create(request):
    """Create new invoice"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                party_id = request.POST.get('party')
                invoice_no = request.POST.get('invoice_no')
                invoice_date = request.POST.get('invoice_date')
                due_date = request.POST.get('due_date')
                items_data = request.POST.get('items_data')
                
                # Validate party
                party = get_object_or_404(Party, id=party_id, user=request.user)
                
                # Parse items data
                items = json.loads(items_data) if items_data else []
                
                if not items:
                    messages.error(request, 'Please add at least one item to the invoice.')
                    return redirect('invoice_create')
                
                # Calculate total amount
                total_amount = sum(Decimal(str(item['amount'])) for item in items)
                
                # Create invoice
                invoice = Invoice.objects.create(
                    user=request.user,
                    name=party.party_name,
                    number=party_id,
                    invoice_no=invoice_no,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    amount=total_amount,
                    status='unpaid'
                )
                
                # Create invoice items
                for item in items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=item['product_id'],
                        product_name=item['product_name'],
                        product_description=item.get('description', ''),
                        quantity=item['quantity'],
                        rate=Decimal(str(item['rate'])),
                        amount=Decimal(str(item['amount']))
                    )
                
                messages.success(request, f'Invoice {invoice_no} created successfully!')
                return redirect('invoice_detail', pk=invoice.pk)
                
        except Exception as e:
            messages.error(request, f'Error creating invoice: {str(e)}')
    
    # Get parties and products for the form
    parties = Party.objects.filter(user=request.user, status=True)
    products = Product.objects.filter(user=request.user, status=True)
    
    # Generate next invoice number
    last_invoice = Invoice.objects.filter(user=request.user).order_by('-id').first()
    next_invoice_no = f"INV-{(last_invoice.id + 1) if last_invoice else 1:06d}"
    
    context = {
        'parties': parties,
        'products': products,
        'next_invoice_no': next_invoice_no,
    }
    
    return render(request, 'invoices/invoice_create.html', context)

@login_required
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    invoice_setting = get_object_or_404(Sales_invoice_settings, user=request.user)

    items = invoice.items.all()

    # Prepare enriched items with tax values
    enriched_items = []
    subtotal = Decimal('0.00')
    total_tax = Decimal('0.00')

    for item in items:
        tax_rate = getattr(item, 'tax_rate', Decimal('0.00'))
        try:
            product = Product.objects.get(id=item.product_id)
            tax_rate = product.tax_rate
            unit = product.unit_of_measure
        except Product.DoesNotExist:
            tax_rate = Decimal('0.00')
            unit = ''

        tax_amount = item.amount * (tax_rate / Decimal('100.00'))
        subtotal += item.amount
        total_tax += tax_amount

        enriched_items.append({
            'item': item,
            'tax_amount': tax_amount,
            'tax_rate': tax_rate,
            'unit': unit,
        })

    total_amount = subtotal + total_tax

    context = {
        'invoice': invoice,
        'invoice_setting': invoice_setting,
        'items': enriched_items,
        'subtotal': subtotal,
        'total_tax': total_tax,
        'total_amount': total_amount,
    }
    return render(request, 'invoices/invoice_detail.html', context)
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
            acc_branch_name=request.POST.get('acc_branch_name'),
            ifsc_code=request.POST.get('ifsc_code'),
            account_no=request.POST.get('account_no'),
            qrcode=request.FILES['qrcode'],
            upload_sign=request.FILES.get('upload_sign')
        )
        instance.save()
        messages.success(request, "Invoice settings saved successfully.")
        return redirect('/invoice_list')  # Change accordingly

    return render(request, 'invoices/create_invoice_setting.html')
@login_required
def invoice_update(request, pk):
    """Update invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update invoice fields
                invoice.invoice_date = request.POST.get('invoice_date')
                invoice.due_date = request.POST.get('due_date')
                invoice.status = request.POST.get('status')
                
                # Update items if provided
                items_data = request.POST.get('items_data')
                if items_data:
                    items = json.loads(items_data)
                    
                    # Delete existing items
                    invoice.items.all().delete()
                    
                    # Create new items
                    total_amount = Decimal('0.00')
                    for item in items:
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
                    
                    invoice.amount = total_amount
                
                invoice.save()
                messages.success(request, 'Invoice updated successfully!')
                return redirect('invoice_detail', pk=invoice.pk)
                
        except Exception as e:
            messages.error(request, f'Error updating invoice: {str(e)}')
    
    # Get data for the form
    parties = Party.objects.filter(user=request.user, status=True)
    products = Product.objects.filter(user=request.user, status=True)
    
    context = {
        'invoice': invoice,
        'parties': parties,
        'products': products,
    }
    
    return render(request, 'invoices/invoice_update.html', context)

@login_required
def invoicesettingedit(request):
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
        invoice_setting.acc_branch_name = request.POST.get('acc_branch_name')
        invoice_setting.ifsc_code = request.POST.get('ifsc_code')
        invoice_setting.account_no = request.POST.get('account_no')

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
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')
        return redirect('invoice_list')
    
    return render(request, 'invoices/invoice_delete.html', {'invoice': invoice})

@login_required
def get_products_ajax(request):
    """AJAX endpoint to get products with their details"""
    products = Product.objects.filter(user=request.user, status=True).values(
        'id', 'product_name', 'category', 'unit_price', 'stock_quantity'
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
    payment=Payment.objects.filter(user=request.user).order_by('-created_at')
    context={'payment':payment}
    return render(request,'Payments/payment.html',context)
@login_required
def payment2_partial(request):
    party=Party.objects.filter(user=request.user)

    if request.method == "POST":
        party_name = request.POST.get("party")
        phone = request.POST.get("phone")
        amount = request.POST.get("amount")
        payment_date = request.POST.get("date")
        payment_mode = request.POST.get("mode")
        notes = request.POST.get("notes")

        # Save to DB (example model)
        Payment.objects.create(
            user=request.user,
            party_name=party_name,
            party_phone=phone,
            amount=amount,
            date=payment_date,
            payment_mode=payment_mode,
            notes=notes,
        )

        messages.success(request, "Payment successfully recorded.")
        return redirect("payments")
    context={'party':party,
             }

    return render(request, "Payments/payment2.html",context)
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
@login_required
def paydelete(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
        return redirect("payments")  # Replace with your payment list view name

    # Optional: If accessed via GET, confirm first (safer)
    return render(request, "Payments/payment_confirm_delete.html", {"payment": payment})


@login_required
def cashbank(request):
    transactions = TotalBalance.objects.filter(user=request.user).order_by('-date')
    total_balance = TotalBalance.objects.aggregate(total=Sum('amount'))['total'] or 0
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
             'accounts':accounts
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