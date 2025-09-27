from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import Customerinbuilt,ShippingPayment


class LoginForm(forms.Form):
    username = forms.CharField(label="Username",max_length=150,widget=forms.TextInput(attrs={'placeholder': 'Enter username'}))
    password = forms.CharField(label="Password",widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}))


class CustomUserCreationForm(DjangoUserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class CustomerinbuiltForm(forms.ModelForm):
    class Meta:
        model = Customerinbuilt
        fields = ['address', 'phonenumber']

class ShippingPaymentForm(forms.ModelForm):
    class Meta:
        model = ShippingPayment
        fields = ["email", "phonenumber", "address"]
