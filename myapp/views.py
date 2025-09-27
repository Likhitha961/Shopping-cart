from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib import messages
from .models import product,customer_cart,ShippingPayment
from .forms import CustomerinbuiltForm, CustomUserCreationForm, LoginForm, ShippingPaymentForm
from .models import Customerinbuilt,ShippingPayment, orders,OrderItem
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import stripe
from django.conf import settings
import uuid


def is_admin(user):
    return user.is_superuser and user.is_staff

def is_customer(user):
    return (not user.is_superuser) and (not user.is_staff)


def index(request):
    products=product.objects.all().order_by("id")
    pagination=Paginator(products,10)
    page_num=request.GET.get("page")
    page_obj=pagination.get_page(page_num)
    # cart=request.session.get('cart',{})
    # cart_count=sum(cart.values())
    return render(request, 'index.html',{
        'page_obj':page_obj})


# ===========================================CART IMPLEMENTATION===========================================================


@login_required
@user_passes_test(is_customer,login_url="login")
@csrf_exempt
def cart(request):
    if request.method=="POST":
        data=json.loads(request.body)
        print(data)
        cart_item=customer_cart.objects.get(id=data["item_id"])   
        print(cart_item)
        cart_item.quantity=data["count"]
        cart_item.save()
    cart_items = customer_cart.objects.filter(customer_id=request.user)
    for item in cart_items:
        item.item_total = item.product_id.price * item.quantity
    total_price=sum(item.product_id.price*item.quantity for item in cart_items)
    cart_count=sum(item.quantity for item in cart_items) 
    return render(request,"cart.html",{"cart_items":cart_items,"total_price":total_price,"cart_count":cart_count})

@login_required
def addtocart(request,product_id):
    # cart=request.session.get('cart',{})
    # cart[str(product_id)]=cart.get(str(product_id),0)+1
    # request.session['cart']=cart
    # return JsonResponse({"cart_count":sum(cart.values())})
    product_obj=get_object_or_404(product,id=product_id)
    cart_items,created=customer_cart.objects.get_or_create(
        customer_id=request.user,
        product_id=product_obj
    )
    if not created:
        cart_items.quantity+=1
        cart_items.save()
    return redirect("index")


def removefromcart(request,product_id):
    # cart=request.session.get('cart',{})
    # if str(product_id) in cart:
    #     del cart[str(product_id)]
    # request.session['cart']=cart
    # return JsonResponse({"cart_count":sum(cart.values())})
    product_obj = get_object_or_404(product, id=product_id)
    cart_items=get_object_or_404(customer_cart,customer_id=request.user,product_id=product_obj)
    cart_items.delete()
    return redirect("cart")


# =======================================login and signup===================================================

def login_view(request):
    next_url=request.GET.get('next') or 'index'
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        next_url=request.POST.get('next') or 'index'
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password")
    return render(request, "login.html", {'form': form,'next': next_url})


def signup(request):
    user_form = CustomUserCreationForm()
    custom_form = CustomerinbuiltForm()
    
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        custom_form = CustomerinbuiltForm(request.POST)
        if user_form.is_valid() and custom_form.is_valid():
            user = user_form.save()
            customer_group, _ = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
            custom = custom_form.save(commit=False)
            custom.user = user
            custom.save()

            raw_password = user_form.cleaned_data['password1']
            user = authenticate(request, username=user.username, password=raw_password)
            if user:
                login(request, user)
                return redirect('index')
            
    
    return render(request, "signup.html", {
        'user_form': user_form,
        'custom_form': custom_form
    })


def home(request):
    user = request.user
    picture = locale = verified = None
    
    if user.is_authenticated:
        try:
            extra_data = user.social_auth.get(provider='google-oauth2').extra_data
            picture = extra_data.get('picture')
            locale = extra_data.get('locale')
            verified = extra_data.get('verified_email') or extra_data.get('email_verified')
        except Exception:
            pass

    return render(request, "home.html", {
        'user': user if user.is_authenticated else None,
        'picture': picture,
        'locale': locale,
        'verified': verified
    })

def logout_view(request):
    logout(request)
    return redirect('login')

# ========================================SHIPPING DETAILS AND PURCHASE DETAILS========================================================

@login_required
def shipping_payment(request):
    try:
        shipping = ShippingPayment.objects.get(user=request.user)
    except ShippingPayment.DoesNotExist:
        shipping = None
    if request.method=="POST":
        shipform=ShippingPaymentForm(request.POST, instance=shipping)
        if shipform.is_valid():
            shipping=shipform.save(commit=False)
            shipping.user=request.user
            shipping.save()
            return redirect("purchaseproduct")
        else:
            messages.error(request,"Given credentials are invalid")
    else:
        shipform = ShippingPaymentForm(instance=shipping)
    return render(request,"shipping.html", {"form": shipform,"username": request.user.username })

@login_required
def purchaseproduct(request):
    cart_items = customer_cart.objects.filter(customer_id=request.user)
    total_price=sum(item.product_id.price * item.quantity for item in cart_items)
    return render(request,"purchase.html",{"cart_items": cart_items,
        "total_price": total_price})


# =============================================================STRIPE IMPLEMENTATION================================================================

stripe.api_key=settings.STRIPE_SECRET_KEY
@login_required
def checkout_session(request):
    cart_items=customer_cart.objects.filter(customer_id=request.user)
    if not cart_items.exists():
        messages.error(request,"Your cart is empty")
        return redirect("cart")
    line_items=[]
    for item in cart_items:
        line_items.append({
            'price_data': {
                        'currency': 'inr',
                        'unit_amount': int(item.product_id.price * 100),
                        'product_data': {
                            'name': item.product_id.name,
                        },
                    },
                    'quantity': item.quantity,
                })
    session=stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri("/success/"), 
        cancel_url=request.build_absolute_uri("/cancel/"), ) 
    return redirect(session.url, code=303) 


class OrderService:
    def __init__(self, user):
        self.user = user
    def create_order(self):
        cart_items=customer_cart.objects.filter(customer_id=self.user)
        if not cart_items.exists():
            return None
        shipping=ShippingPayment.objects.filter(user=self.user).first()
        order=orders.objects.create(
            user=self.user,
            shipping=shipping,
            total_price=sum(item.product_id.price*item.quantity for item in cart_items),
            paid=True
        )
        for i in cart_items:
            OrderItem.objects.create(
                order=order,
                product=i.product_id,
                price=i.product_id.price,
                quantity=i.quantity
            )
        cart_items.delete()
        return order

@login_required 
def success(request):
      order=OrderService(request.user).create_order()
      return render(request, "success.html", {"order": order})

@login_required 
def cancel(request):
    return render(request,"cancel.html")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")

        try:
            user=User.objects.get(email=email)
        except User.DoesNotExist:
            return HttpResponse(status=200)

        order=OrderService(user).create_order()
    return HttpResponse(status=200)


# =======================================================Admin Dashboard===============================================================


def admin_(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")

        user=authenticate(request,username=username,password=password)

        if user is not None and user.is_superuser:
            login(request,user)
            return redirect("admin_dashboard")
        else:
            messages.error(request,"Invalid credentials about the user")
    return render(request,"admin_.html")


@user_passes_test(is_admin,login_url="admin_")
def admin_dashboard(request):
    return render(request,"admin_dashboard.html")


def myorders(request):
      if request.user.is_authenticated:
        order=orders.objects.all().select_related("user", "shipping")
        return render(request, "orders.html", {"orders": order})
      else:
        return render(request, "orders.html", {"orders": []})


def productss(request):
    products=product.objects.all()
    return render(request,"products.html",{"products": products})


def orders_delete(request,item_id):
    item=get_object_or_404(OrderItem,id=item_id)
    item.delete()
    return redirect("myorders")

def product_delete(request,item_id):
    prod=get_object_or_404(product,id=item_id)
    prod.delete()
    return redirect("productss")


def product_edit(request,item_id):
    prod=get_object_or_404(product,id=item_id)
    if request.method=="POST":
        prod.name=request.POST.get("name")
        prod.price=request.POST.get("price")
        prod.save()
        return redirect("productss")
    return render(request,"products_edit.html",{"product":prod})

def order_edit(request,item_id):
    item=get_object_or_404(OrderItem,id=item_id)
    if request.method=="POST":
        item.name=request.POST.get("name")
        item.price=request.POST.get("price")
        item.quantity=request.POST.get("quantity")
        item.save()
        return redirect("myorders")
    return render(request,"orders_edit.html",{"item":item})



# ============================================PHONEPE====================================================


import base64  
import shortuuid
import hashlib
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

def calculate_sha256_string(input_string):
    sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())
    sha256.update(input_string.encode('utf-8'))
    return sha256.finalize().hex()
 
def base64_encode(input_dict):
    json_data = json.dumps(input_dict)
    data_bytes = json_data.encode('utf-8')
    return base64.b64encode(data_bytes).decode('utf-8')

def create_payment(request, amount, transaction_id):
        return{
            "merchantId": "PGTESTPAYUAT86",
            "merchantTransactionId": transaction_id,
            "merchantUserId": f"MUID{request.user.id if request.user.is_authenticated else 'GUEST'}",
            "amount": int(amount * 100),
            "redirectUrl": request.build_absolute_uri('/validate_payment/'),
            "redirectMode": "POST",
            "callbackUrl": request.build_absolute_uri('/cart'),
            "mobileNumber": "9999999999",
            "paymentInstrument": {"type": "PAY_PAGE"}
        }


def phonepay_payment(request):
    cart_items=customer_cart.objects.filter(customer_id=request.user)
    amount=sum(item.product_id.price * item.quantity for item in cart_items)

    if amount<=0:
        messages.error("Your cart is empty")
        return redirect('cart')
    try:
            transaction_id=shortuuid.uuid()
            payload=create_payment(request, amount,transaction_id)
            print(payload)
            base64String=base64_encode(payload)

            merchant_salt = "96434309-7796-489d-8924-ab56988a6076"
            mainString=base64String+"/pg/v1/pay"+ merchant_salt
            sha256Val= calculate_sha256_string(mainString)
            checkSum=sha256Val+ '###1'

            response=requests.post('https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/pay',
                headers={'Content-Type':'application/json',
                        'X-VERIFY': checkSum,
                        'accept':'application/json'
                        },
                        json={'request':base64String},
                        timeout=30
            )

            responsedata=response.json()
            print("PhonePe API Response:", json.dumps(responsedata, indent=4))
            
            if responsedata.get('success') and 'data' in responsedata and 'instrumentResponse' in responsedata['data']:
                return redirect(responsedata['data']['instrumentResponse']['redirectInfo']['url'])
            else:
                messages.error("Invalid")
                return redirect('cart')
            
    except Exception as e:
        messages.error(request, f"Something went wrong: {e}")
        return redirect("cart")


@csrf_exempt
def validate_payment(request):
    if request.method == "POST":
        merchant_id = request.POST.get("merchantId")
        status_code = request.POST.get("code") 
    else:
        merchant_id = request.GET.get("merchantId")
        status_code = request.GET.get("code")  

    if status_code == "PAYMENT_SUCCESS":
        messages.success(request, "Payment successful via PhonePe!")
        return redirect("success") 
    elif status_code == "PAYMENT_FAILURE":
        messages.error(request, "Payment was cancelled or failed.")
        return redirect("cancel") 
    elif status_code == "PAYMENT_PENDING":
        messages.warning(request, "Your payment is still pending. Please wait a moment and refresh.")
        return redirect("cart") 

    messages.error(request, "Unable to verify payment status.")
    return redirect("cancel")























# def products_list(request):
#     products=product.object.all()
#     # cart=request.session.get('cart',{})
#     cart_count=sum(cart.values())
#     return render(request,"cart.html",{
#         'products': products,
#         'cart_count': cart_count
#     })






# from django.contrib.auth.models import User

# user = User.objects.get(email="yourgoogleemail@gmail.com")
# user.is_staff = True   # allow to appear in admin user list
# user.save()




# def theme(request,theme_choice):
#     if theme_choice not in ["dark","light"]:
#         return HttpResponse("Invalid choice")

#     response=redirect("Show_theme")
#     response.set_cookie("theme",theme_choice,max_age=27*60*60)
#     return response
# def get_theme(request):
#     theme=request.COOKIES.get("theme","light")
#     return render(request,"base.html",{"theme":theme})











