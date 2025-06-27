from datetime import date, timedelta
from .models import Product 

def expiring_soon_products(request):
    expiring_soon = []
    expiring_soon_count = 0

    if request.user.is_authenticated:
        try:
            today = date.today()
            three_days_later = today + timedelta(days=3)
            expiring_soon = Product.objects.filter(user=request.user,expiry_date__range=[today, three_days_later])
            expiring_soon_count = expiring_soon.count()
        except Exception as e:
            # Log error if needed
            pass

    return {
        'expiring_soon_products': expiring_soon,
        'expiring_soon_count':expiring_soon_count
    }