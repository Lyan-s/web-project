from django.shortcuts import render,redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from .forms import TransactionForm ,RegisterForm ,CategoryForm
from .models import Transaction, Category
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncMonth

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
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'expenses/add_transaction.html', {'form': form})
@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user)

    search_query = request.GET.get('search')
    category_filter = request.GET.get('category')
    date_filter = request.GET.get('date')

    if search_query:
        transactions = transactions.filter(title__icontains=search_query)

    if category_filter:
        transactions = transactions.filter(category__id=category_filter)

    if date_filter:
        transactions = transactions.filter(date_created__date=date_filter)

    transactions = transactions.order_by('-date_created')
    categories = Category.objects.all()

    context = {
        'transactions': transactions,
        'categories': categories,
    }
    return render(request, 'expenses/transaction_list.html', context)

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'expenses/edit_transaction.html',{'form', form})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    transaction.delete()
    return redirect('transaction_list')

from django.db.models import Sum

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)

    total_income = transactions.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    recent_transactions = transactions.order_by('-date_created')[:5]

    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'expenses/dashboard.html', context)



@login_required
def reports(request):
    transactions = Transaction.objects.filter(user=request.user)

    monthly_income = (
        transactions.filter(type='Income')
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    monthly_expenses = (
        transactions.filter(type='Expense')
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    category_spending = (
        transactions.filter(type='Expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    total_income = transactions.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'category_spending': category_spending,
        'balance': balance,
    }
    return render(request, 'expenses/reports.html', context)


@login_required
def add_category(request):
    next_page = request.GET.get('next') or request.POST.get('next', 'dashboard')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(next_page)
    else:
        form = CategoryForm()
    return render(request, 'expenses/add_category.html', {'form': form, 'next': next_page})