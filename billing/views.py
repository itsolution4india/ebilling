from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Party, Product, Invoice, InvoiceItem, Payment, TotalBalance
from .serializers import PartySerializer, ProductSerializer, InvoiceSerializer, InvoiceListSerializer, InvoiceItemSerializer, PaymentSerializer
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from rest_framework.permissions import AllowAny
import random
import string

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
        print("Raw body:", request.body)  # Add this for debugging
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        print("JSON decode error:", e)
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
    return render(request, 'products/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.product_code = generate_product_code()
            product.hsn_code = generate_hsn_code()
            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form, 'action': 'Add'})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'action': 'Update'})

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
    return render(request, 'party/party_list.html', {'parties': parties})

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
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})

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
    invoice_amount = invoice.amount
    sgst_amount = invoice_amount * Decimal('0.06')
    cgst_amount = invoice_amount * Decimal('0.06')
    total_amount = invoice_amount + sgst_amount + cgst_amount

    context = {
        'invoice': invoice,
        'invoice_amount': invoice_amount,
        'sgst_amount': sgst_amount,
        'cgst_amount': cgst_amount,
        'total_amount': total_amount,
    }
    return render(request, 'invoices/invoice_detail.html', context)

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
        'id', 'product_name', 'description', 'unit_price', 'stock_quantity'
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