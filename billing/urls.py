from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('api/auth/login/', views.login_view, name='login'),
    
    # Parties
    path('api/auth/parties/', views.party_list, name='party-list'),
    path('api/auth/parties/store/', views.party_store, name='party-store'),
    path('api/auth/parties/edit/<int:party_id>/', views.party_edit, name='party-edit'),
    path('api/auth/parties/update/<int:party_id>/', views.party_update, name='party-update'),
    path('api/auth/parties/delete/<int:party_id>/', views.party_delete, name='party-delete'),
    
    # Products
    path('api/auth/products/', views.product_list, name='product-list'),
    path('api/auth/products/store/', views.product_store, name='product-store'),
    path('api/auth/products/edit/<int:product_id>/', views.product_edit, name='product-edit'),
    path('api/auth/products/update/<int:product_id>/', views.product_update, name='product-update'),
    path('api/auth/products/delete/<int:product_id>/', views.product_delete, name='product-delete'),
    
    # Invoice URLs
    path('api/auth/invoices/', views.api_invoice_list, name='invoice-list'),
    path('api/auth/invoices/store/', views.invoice_store, name='invoice-store'),
    path('api/auth/invoices/<int:invoice_id>/', views.invoice_detail, name='invoice-detail'),
    path('api/auth/invoices/edit/<int:invoice_id>/', views.invoice_edit, name='invoice-edit'),
    path('api/auth/invoices/update/<int:invoice_id>/', views.invoice_update, name='invoice-update'),
    path('api/auth/invoices/delete/<int:invoice_id>/', views.invoice_delete, name='invoice-delete'),
    path('api/auth/invoices/<int:invoice_id>/status/', views.invoice_status_update, name='invoice-status-update'),
    
    # Invoice Items URLs
    path('api/auth/invoices/<int:invoice_id>/items/', views.invoice_items, name='invoice-items'),
    path('api/auth/invoices/<int:invoice_id>/items/add/', views.invoice_item_add, name='invoice-item-add'),
    path('api/auth/invoices/<int:invoice_id>/items/<int:item_id>/delete/', views.invoice_item_delete, name='invoice-item-delete'),
    
    # Payment URLs
    path('api/auth/payments/', views.payment_list, name='payment-list'),
    path('api/auth/payments/store/', views.payment_store, name='payment-store'),
    path('api/auth/payments/edit/<int:payment_id>/', views.payment_edit, name='payment-edit'),
    path('api/auth/payments/update/<int:payment_id>/', views.payment_update, name='payment-update'),
    path('api/auth/payments/delete/<int:payment_id>/', views.payment_delete, name='payment-delete'),
    path('api/auth/payments/party/<str:party_name>/', views.payment_by_party, name='payment-by-party'),
    path('api/auth/payments/statistics/', views.payment_statistics, name='payment-statistics'),
    
    # Djnago views
    path('', views.login_page, name='login-page'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Product CRUD views
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # partie
    path('parties/', views.party_list, name='party_list'),
    path('parties/add/', views.party_create, name='party_create'),
    path('parties/<int:pk>/edit/', views.party_update, name='party_update'),
    path('parties/<int:pk>/delete/', views.party_delete, name='party_delete'),
    
    # Invoice URLs
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoice-setting/', views.invoicesetting, name='invoicesetting'),
    path('invoice-setting-edit/', views.invoicesettingedit, name='invoicesettingedit'),
    path('invoices/add/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_update, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('payments/',views.payments,name='payments'),
    path("payments/load-payment2/",views.payment2_partial, name="load_payment2"),
    path("payments/<int:pk>/edit",views.payedit, name="payedit"),
    path("payments/<int:pk>/delete",views.paydelete, name="paydelete"),
    path("cashbank/",views.cashbank, name="cashbank"),
    path("cashbank/<int:pk>/edit",views.cashedit, name="cashedit"),
    path("cashbank/<int:pk>/delete",views.cashdelete, name="cashdelete"),
    path('logout/', views.logout_view, name='logout_view'),
    path("ajax/set-invoice-paid/", views.set_invoice_paid, name="set_invoice_paid"),
    # AJAX endpoints
    path('ajax/products/', views.get_products_ajax, name='get_products_ajax'),
    path('ajax/party/<int:party_id>/', views.get_party_details_ajax, name='get_party_details_ajax'),
]