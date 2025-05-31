from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    
    # Parties
    path('parties/', views.party_list, name='party-list'),
    path('parties/store/', views.party_store, name='party-store'),
    path('parties/edit/<int:party_id>/', views.party_edit, name='party-edit'),
    path('parties/update/<int:party_id>/', views.party_update, name='party-update'),
    path('parties/delete/<int:party_id>/', views.party_delete, name='party-delete'),
    
    # Products
    path('products/', views.product_list, name='product-list'),
    path('products/store/', views.product_store, name='product-store'),
    path('products/edit/<int:product_id>/', views.product_edit, name='product-edit'),
    path('products/delete/<int:product_id>/', views.product_delete, name='product-delete'),
]