from django.shortcuts import render,redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from .forms import TransactionForm
# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'expenses/register.html', {'form': form})
def home(request):
    return render(request, 'home.html')

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.Post)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'expenses/add_transaction.html', {'form': form})