from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import DailySpending, Profile


def user_login(request):
    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")

        # Check if email exists
        if not User.objects.filter(email=email).exists():
            messages.error(
                request, "This email is not registered. Please create an account first."
            )
            return redirect("login")

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect("login")

        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name}!")
        return redirect("dashboard")

    return render(request, "login.html")

def user_logout(request):
    logout(request)
    return redirect("home")
    
def edit_transaction(request, id):
    expense = get_object_or_404(DailySpending, id=id, user=request.user)

    if request.method == "POST":
        expense.item = request.POST.get("item")
        expense.amount = request.POST.get("amount")
        expense.date = request.POST.get("date")

        expense.save()

        messages.success(request, "Transaction updated successfully.")

        return redirect("transaction_log")

    return render(request, "edit_transaction.html", {"expense": expense})
def delete_transaction(request, id):
    expense = get_object_or_404(DailySpending, id=id, user=request.user)

    expense.delete()

    messages.success(request, "Transaction deleted successfully.")

    return redirect("transaction_log")
def home(request):
    return render(request, "home.html")


def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "home.html")

    expenses = DailySpending.objects.filter(user=request.user)

    total_spending = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    today_spending = (
        expenses.filter(date=timezone.now().date()).aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )

    current_month = timezone.now().month
    current_year = timezone.now().year

    monthly_spending = (
        expenses.filter(date__month=current_month, date__year=current_year).aggregate(
            Sum("amount")
        )["amount__sum"]
        or 0
    )

    recent_expenses = expenses.order_by("-date", "-id")[:5]

    context = {
        "total_spending": total_spending,
        "today_spending": today_spending,
        "monthly_spending": monthly_spending,
        "recent_expenses": recent_expenses,
        "all_spending": expenses.order_by("-date"),
    }

    return render(request, "dashboard.html", context)


def register_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")

        # 1. Validation: Ensure phone number is strictly digits
        if not phone.isdigit():
            messages.error(
                request, "Registration failed: Phone number must contain only numbers."
            )
            return redirect("home")

        # 2. Database Check: Check if Email has been used before
        if User.objects.filter(email=email).exists():
            messages.error(
                request, "Registration failed: This email is already registered."
            )
            return redirect("home")

        # 3. Database Check: Check if Phone has been used before
        if Profile.objects.filter(phone=phone).exists():
            messages.error(
                request, "Registration failed: This phone number is already registered."
            )
            return redirect("home")

        # 4. Save to Database: Create User account (Username defaults to email)
        new_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Create corresponding profile to link the phone number
        Profile.objects.create(user=new_user, phone=phone)

        # Automatically log the user in after registration
        login(request, new_user)
        messages.success(
            request, "Account created successfully! You are now logged in."
        )

    return redirect("dashboard")

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if User.objects.filter(email=email).exists():
            messages.success(
                request, "Password reset instructions have been sent to your email."
            )
        else:
            messages.error(request, "No account was found with that email address.")

        return redirect("forgot_password")

    return render(request, "forgot_password.html")

def add_spending(request):
    if request.method == "POST" and request.user.is_authenticated:
        amount = request.POST.get("amount")
        item = request.POST.get("item")
        category = request.POST.get("category")
        date = request.POST.get("date")

        spending = DailySpending.objects.create(
            user=request.user,
            amount=amount,
            item=item,
            category=category,
            date=date,
        )

        print("User:", request.user)
        print("Saved spending ID:", spending.id)

        messages.success(request, "Expense logged successfully!")
        
        return redirect("dashboard")



def transaction_log(request):
    if not request.user.is_authenticated:
        return redirect("home")

    transactions = DailySpending.objects.filter(user=request.user).order_by("-date")

    return render(
        request,
        "transaction_log.html",
        {"transactions": transactions},
    )
    
def categories(request):

    if not request.user.is_authenticated:
        return redirect("login")

    categories = (
        DailySpending.objects
        .filter(user=request.user)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    return render(
        request,
        "categories.html",
        {"categories": categories}
    )