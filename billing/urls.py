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
    path('products/update/<int:product_id>/', views.product_update, name='product-update'),
    path('products/delete/<int:product_id>/', views.product_delete, name='product-delete'),
    
    # Invoice URLs
    path('invoices/', views.invoice_list, name='invoice-list'),
    path('invoices/store/', views.invoice_store, name='invoice-store'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice-detail'),
    path('invoices/edit/<int:invoice_id>/', views.invoice_edit, name='invoice-edit'),
    path('invoices/update/<int:invoice_id>/', views.invoice_update, name='invoice-update'),
    path('invoices/delete/<int:invoice_id>/', views.invoice_delete, name='invoice-delete'),
    path('invoices/<int:invoice_id>/status/', views.invoice_status_update, name='invoice-status-update'),
    
    # Invoice Items URLs
    path('invoices/<int:invoice_id>/items/', views.invoice_items, name='invoice-items'),
    path('invoices/<int:invoice_id>/items/add/', views.invoice_item_add, name='invoice-item-add'),
    path('invoices/<int:invoice_id>/items/<int:item_id>/delete/', views.invoice_item_delete, name='invoice-item-delete'),
    
    # Payment URLs
    path('payments/', views.payment_list, name='payment-list'),
    path('payments/store/', views.payment_store, name='payment-store'),
    path('payments/edit/<int:payment_id>/', views.payment_edit, name='payment-edit'),
    path('payments/update/<int:payment_id>/', views.payment_update, name='payment-update'),
    path('payments/delete/<int:payment_id>/', views.payment_delete, name='payment-delete'),
    path('payments/party/<str:party_name>/', views.payment_by_party, name='payment-by-party'),
    path('payments/statistics/', views.payment_statistics, name='payment-statistics'),
    
    # Dashboard URLs
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('dashboard/transactions/', views.dashboard_transactions, name='dashboard-transactions'),
]