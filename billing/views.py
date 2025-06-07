from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Party, Product, Branch
from .serializers import PartySerializer, ProductSerializer, BranchSerializer
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from rest_framework.permissions import AllowAny

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
    serializer = PartySerializer(data=request.data)
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
        serializer = PartySerializer(party, data=request.data)
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