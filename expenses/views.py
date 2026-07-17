from django.shortcuts import render,redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from .forms import TransactionForm ,RegisterForm ,CategoryForm
from .models import Transaction, Category
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncMonth
import csv
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from .models import Transaction, Category, Profile
from .forms import TransactionForm, RegisterForm, CategoryForm, ProfileForm


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
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    transactions = Transaction.objects.filter(user=request.user)
    total_income = transactions.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses
    total_transactions = transactions.count()

    context = {
        'form': form,
        'profile': profile,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'total_transactions': total_transactions,
    }
    return render(request, 'expenses/profile.html', context)

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Amount', 'Type', 'Category', 'Description', 'Date'])

    transactions = Transaction.objects.filter(user=request.user).order_by('-date_created')
    for transaction in transactions:
        writer.writerow([
            transaction.title,
            transaction.amount,
            transaction.type,
            transaction.category,
            transaction.description,
            transaction.date_created.strftime('%Y-%m-%d %H:%M'),
        ])

    return response

@login_required
def export_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Smart Expense Tracker - Report", styles['Title']))
    elements.append(Spacer(1, 20))

    # Summary
    transactions = Transaction.objects.filter(user=request.user)
    total_income = transactions.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    summary_data = [
        ['Total Income', f'KES {total_income:,.2f}'],
        ['Total Expenses', f'KES {total_expenses:,.2f}'],
        ['Balance', f'KES {balance:,.2f}'],
    ]

    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0d1b2a')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#00e5ff')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#0d1b2a'), colors.HexColor('#0a0a1a')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#00d4ff')),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Transactions table
    elements.append(Paragraph("All Transactions", styles['Heading2']))
    elements.append(Spacer(1, 10))

    data = [['Title', 'Amount', 'Type', 'Category', 'Date']]
    for t in transactions.order_by('-date_created'):
        data.append([
            t.title,
            f'KES {t.amount:,.2f}',
            t.type,
            str(t.category) if t.category else 'Uncategorized',
            t.date_created.strftime('%Y-%m-%d'),
        ])

    table = Table(data, colWidths=[120, 100, 80, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#090979')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00e5ff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f0f0'), colors.white]),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0a0a1a')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#00d4ff')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="smart_expense_report.pdf"'
    return response

from .models import Transaction, Category, Budget
from .forms import RegisterForm, TransactionForm, CategoryForm, BudgetForm

@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user)
    alerts = []

    for budget in budgets:
        spent = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            type='Expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        percentage = (spent / budget.limit * 100) if budget.limit > 0 else 0

        alerts.append({
            'budget': budget,
            'spent': spent,
            'percentage': round(percentage, 1),
            'remaining': budget.limit - spent,
            'over_budget': spent > budget.limit,
            'near_limit': percentage >= 80 and spent <= budget.limit,
        })

    return render(request, 'expenses/budget_list.html', {'alerts': alerts})


@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('budget_list')
    else:
        form = BudgetForm()
    return render(request, 'expenses/add_budget.html', {'form': form})


@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    return redirect('budget_list')