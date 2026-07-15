from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Transaction

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

class TransactionForm(forms.ModelForm):
    class Meta:
        model= Transaction
        fields = ['title' , 'amount', 'type', 'category', 'description']