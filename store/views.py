from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomerRegistrationForm
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Payment, Receipt
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem, Product
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Payment, Receipt, ShippingAddress

import uuid

# Create your views here.

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})

def product_list(request, category_id=None):
    if category_id:
        # If a category was clicked, filter the products
        category = get_object_or_404(Category, id=category_id)
        products = Product.objects.filter(category=category)
    else:
        # Otherwise, show everything
        products = Product.objects.all()
        
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, pk):
    # This process shows details for a specific item
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

def register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('product_list')

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    if not items.exists():
        return redirect('product_list')
        
    if request.method == 'POST':
        total = sum(item.product.price * item.quantity for item in items)
        
        # Capture the selected payment method and save it in the session
        payment_method = request.POST.get('payment_method', 'Card')
        request.session['payment_method'] = payment_method
        
        # 1. Create the Shipping Address in the database
        shipping_address = ShippingAddress.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            phone_number=request.POST.get('phone_number'),
            street_address=request.POST.get('street_address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            pincode=request.POST.get('pincode')
        )
        
        # 2. Create the Order and link the new address!
        order = Order.objects.create(
            user=request.user, 
            total_amount=total, 
            shipping_address=shipping_address  # Replaced the old 'address' field
        )
        
        for item in items:
            OrderItem.objects.create(
                order=order, product=item.product, 
                price=item.product.price, quantity=item.quantity
            )
            item.product.stock_quantity -= item.quantity
            item.product.save()
        
        items.delete()
        return redirect('process_payment', order_id=order.id)

    total_amount = sum(item.product.price * item.quantity for item in items)
    return render(request, 'store/checkout.html', {'items': items, 'total_amount': total_amount})


@login_required
def process_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Retrieve the payment method chosen in the checkout step
    payment_method = request.session.get('payment_method', 'Debit Card')
    
    payment = Payment.objects.create(
        order=order,
        payment_method_id=str(uuid.uuid4()),
        payment_type=payment_method, # Dynamically sets Card, UPI, or COD
        status="Success" 
    )
    
    order.status = "Paid"
    order.save()
    
    receipt = Receipt.objects.create(
        receipt_id=f"REC-{uuid.uuid4().hex[:8].upper()}",
        user=request.user,
        order=order,
        payment=payment,
        tax_details=order.total_amount * Decimal('0.05') 
    )
    
    return redirect('view_receipt', receipt_id=receipt.receipt_id)

@login_required
def view_receipt(request, receipt_id):
    receipt = get_object_or_404(Receipt, receipt_id=receipt_id, user=request.user)
    return render(request, 'store/receipt.html', {'receipt': receipt})

@login_required
def order_history(request):
    # Fetch all orders for this user, newest first
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
def order_history(request):
    # Fetch all orders for this user, newest first
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # --- PORTFOLIO SIMULATION LOGIC ---
    # This automatically updates the status based on how long ago the order was placed!
    # (Speeds up a 5-day delivery into 5 minutes for presentation purposes)
    now = timezone.now()
    time_passed = now - order.order_date
    
    if order.status != 'Delivered': 
        if time_passed > timedelta(minutes=5): 
            order.status = 'Delivered'
        elif time_passed > timedelta(minutes=3):
            order.status = 'Out for Delivery'
        elif time_passed > timedelta(minutes=2):
            order.status = 'Shipped'
        elif time_passed > timedelta(minutes=1):
            order.status = 'Processing'
        order.save() # Save the simulated progress
    # -----------------------------------
        
    return render(request, 'store/track_order.html', {'order': order})