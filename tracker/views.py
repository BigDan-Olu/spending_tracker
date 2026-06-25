import random
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
from tracker.utils import send_brevo_email

from .models import Category, DailySpending, EmailOTP, Profile
from django.contrib.auth import get_user_model

User = get_user_model()


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


def generate_otp():
    return str(random.randint(100000, 999999))


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


def verify_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")

        print("ENTERED OTP:", otp)

        data = request.session.get("registration_data")

        print("SESSION:", data)

        if not data:
            messages.error(request, "Registration session expired.")
            return redirect("home")

        records = EmailOTP.objects.filter(email=data["email"])

        print("OTP RECORDS:", list(records.values()))

        record = records.filter(otp=otp).last()

        print("MATCHED RECORD:", record)

        if record:
            user = User.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )

            Profile.objects.create(user=user, phone=data["phone"])

            login(request, user)

            EmailOTP.objects.filter(email=data["email"]).delete()

            request.session.pop("registration_data", None)

            messages.success(request, "Account verified successfully!")

            return redirect("dashboard")

        messages.error(request, "Invalid OTP.")

    return render(request, "verify_otp.html")

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

        print("EMAIL:", email)
        print("PHONE:", phone)

        print("EMAIL EXISTS:", User.objects.filter(email=email).exists())
        print("PHONE EXISTS:", Profile.objects.filter(phone=phone).exists())

        if not phone.isdigit():
            print("FAILED PHONE VALIDATION")
            messages.error(
                request, "Registration failed: Phone number must contain only numbers."
            )
            return redirect("home")

        if User.objects.filter(email=email).exists():
            print("EMAIL ALREADY EXISTS")
            messages.error(
                request, "Registration failed: This email is already registered."
            )
            return redirect("home")

        if Profile.objects.filter(phone=phone).exists():
            print("PHONE ALREADY EXISTS")
            messages.error(
                request, "Registration failed: This phone number is already registered."
            )
            return redirect("home")

        otp = str(random.randint(100000, 999999))
        print("OTP:", otp)

        EmailOTP.objects.create(email=email, otp=otp)
        print("OTP SAVED")

        request.session["registration_data"] = {
            "email": email,
            "phone": phone,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        }

        print("SESSION SAVED")

        response = send_brevo_email(
            email,
            "Verify Your Spending Tracker Account",
            f"<h2>Your verification code is {otp}</h2>",
        )

        print("EMAIL STATUS:", response.status_code)
        print("EMAIL BODY:", response.text)

        messages.success(request, "Verification code sent to your email.")

        return redirect("verify_otp")

    return redirect("home")


def forgot_password(request):

    if request.method == "POST":
        email = request.POST.get("email")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "No account found with that email.")
            return redirect("forgot_password")

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        token = default_token_generator.make_token(user)

        reset_link = (
            f"{settings.SITE_URL}"
            f"{reverse('reset_password', kwargs={'uidb64': uid, 'token': token})}"
        )

        response = send_brevo_email(
            email,
            "Reset Your Password",
            f"""
            <h2>Password Reset</h2>

            <p>Click the link below to reset your password:</p>

            <a href="{reset_link}">
                Reset Password
            </a>
            """,
        )
        print("RESET LINK:", reset_link)
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        messages.success(request, "Password reset link sent to your email.")

        return redirect("forgot_password")

    return render(request, "forgot_password.html")


def reset_password(request, uidb64, token):

    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))

    except:
        uid = None

    user = None

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

    except:
        pass

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")

            user.set_password(password)
            user.save()

            messages.success(request, "Password reset successful. Login now.")

            return redirect("login")

        return render(request, "reset_password.html")

    return render(request, "reset_invalid.html")


def add_spending(request):
    if request.method == "POST" and request.user.is_authenticated:
        amount = request.POST.get("amount")
        item = request.POST.get("item")
        date = request.POST.get("date")

        category_name = request.POST.get("category")

        category, created = Category.objects.get_or_create(name=category_name)

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
        DailySpending.objects.filter(user=request.user)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    return render(request, "categories.html", {"categories": categories})

    return render(request, "categories.html", {"categories": categories})
