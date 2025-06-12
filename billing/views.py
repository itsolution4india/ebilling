from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Party, Product, Invoice, InvoiceItem, Payment
from .serializers import PartySerializer, ProductSerializer, InvoiceSerializer, InvoiceListSerializer, InvoiceItemSerializer, PaymentSerializer
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from rest_framework.permissions import AllowAny
import random
import string

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
    """Create a new invoice"""
    data = request.data.copy()
    
    # Handle user field - expect user_id from frontend or user from authenticated request
    if 'user_id' in data:
        data['user'] = data.pop('user_id')
    elif hasattr(request, 'user') and request.user.is_authenticated:
        data['user'] = request.user.id
    
    # Generate random invoice ID if not provided
    if not data.get('invoice_no'):
        data['invoice_no'] = generate_random_invoice_id()
    
    serializer = InvoiceSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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
    