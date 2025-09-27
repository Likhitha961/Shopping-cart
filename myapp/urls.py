from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from myapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),

    path('addtocart/<int:product_id>',views.addtocart,name='addtocart'),
    path('removefromcart/<int:product_id>',views.removefromcart,name='removefromcart'),
    path('cart/', views.cart, name='cart'),

    path('admin_/',views.admin_,name='admin_'),
    path("admin_dashboard/",views.admin_dashboard,name="admin_dashboard"),
    path('myorders/',views.myorders,name='myorders'),
    path('myproducts/',views.productss,name="productss"),
    path('OrderItem/<int:item_id>/delete/',views.orders_delete,name="orders_delete"),
    path("product/<int:item_id>/delete/",views.product_delete,name="product_delete"),
    path("product/<int:item_id>/edit/",views.product_edit,name="product_edit"),
    path("order/<int:item_id>/edit/",views.order_edit,name="order_edit"),

    path('shippayment/',views.shipping_payment,name="shipping_payment"),
    path('purchaseproduct/',views.purchaseproduct,name="purchaseproduct"),
    path('checkout_session/',views.checkout_session,name="checkout_session"),
    path('success/',views.success,name="success"),
    path('cancel/',views.cancel,name="cancel"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),

    path('phonepay_payment/',views.phonepay_payment,name="phonepay_payment"),
    path('validate_payment/',views.validate_payment,name="validate_payment"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
