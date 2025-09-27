from django.db import models
from django.contrib.auth.models import User


class Customerinbuilt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phonenumber = models.CharField(max_length=15)
    address = models.TextField(max_length=255)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

class product(models.Model):
    name=models.CharField(max_length=100)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    image=models.ImageField(upload_to='products/')
    def __str__(self):
        return self.name

class customer_cart(models.Model):
    customer_id=models.ForeignKey(User,on_delete=models.CASCADE,to_field="id",related_name="Customer_details")
    product_id=models.ForeignKey(product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)

class ShippingPayment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    phonenumber = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.email
    
    
class orders(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    shipping=models.ForeignKey(ShippingPayment,on_delete=models.CASCADE)
    createdat=models.DateTimeField(auto_now_add=True)
    total_price=models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    paid=models.BooleanField(default=False)
    
    def __str__(self):
        return f"Order{self.id} by {self.user.username}"
    
class OrderItem(models.Model):
    order=models.ForeignKey(orders,on_delete=models.CASCADE,related_name="items")
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    price=models.DecimalField(max_digits=10,decimal_places=2,default=0.00)

    def __str__(self):
        return f"Order{self.product.name} - {self.product.price}"
