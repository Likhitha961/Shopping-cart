from .models import customer_cart

def carter(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_items = customer_cart.objects.filter(customer_id=request.user)
        cart_count = sum(item.quantity for item in customer_cart.objects.filter(customer_id=request.user))
    return {"cart_count": cart_count}
