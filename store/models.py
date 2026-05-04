from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    is_customer = models.BooleanField(default=True)
    is_vendor = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Add this to allow vendors to log into the admin dashboard
    @property
    def is_staff(self):
        return self.is_superuser or self.is_vendor

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    # Matches D2 Category in DFD [cite: 104]

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    
    # These match your ER attributes [cite: 51, 52, 53, 55, 56, 57]

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True) # Matches Created_At in ER [cite: 20]

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='Order Placed', choices=[
        ('Order Placed', 'Order Placed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered')
    ])

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

class Payment(models.Model):
    # Matches Payment_Method in ER
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method_id = models.CharField(max_length=100) # cite: 46
    payment_type = models.CharField(max_length=50) # cite: 60
    status = models.CharField(max_length=20) # cite: 67
    date_paid = models.DateTimeField(auto_now_add=True)

class Receipt(models.Model):
    # Matches Receipt entity in ER
    receipt_id = models.CharField(max_length=100, unique=True) # cite: 71
    user = models.ForeignKey(User, on_delete=models.CASCADE) # cite: 11
    order = models.OneToOneField(Order, on_delete=models.CASCADE) # cite: 44
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE) # cite: 69
    tax_details = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # cite: 68
    generated_at = models.DateTimeField(auto_now_add=True)

