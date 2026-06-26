import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from tracker.utils import send_brevo_email

from .models import Category, DailySpending, EmailOTP, PendingRegistration, Profile

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


@require_POST
def resend_otp(request):
    email = request.POST.get("email")

    if not email:
        return JsonResponse(
            {"success": False, "message": "Email is required."},
            status=400,
        )

    try:
        pending = PendingRegistration.objects.get(email=email)
    except PendingRegistration.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "No pending registration found."},
            status=404,
        )

    # Generate a new OTP
    otp = f"{random.randint(100000, 999999)}"

    pending.otp = otp
    pending.created_at = timezone.now()
    pending.save(update_fields=["otp", "created_at"])

    response = send_brevo_email(
        pending.email,
        "Verify Your Spending Tracker Account",
        f"""
        <h2>Email Verification</h2>

        <p>Your new verification code is:</p>

        <h1>{otp}</h1>

        <p>This code expires in <strong>10 minutes</strong>.</p>
        """,
    )

    if response.status_code not in (200, 201):
        return JsonResponse(
            {"success": False, "message": "Unable to send OTP email."},
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "message": "A new verification code has been sent to your email.",
        }
    )


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
        email = request.POST.get("email")
        otp = request.POST.get("otp")

        pending = PendingRegistration.objects.filter(
            email=email,
            otp=otp,
        ).first()

        if not pending:
            messages.error(request, "Invalid email or OTP.")
            return redirect("verify_otp")

        if pending.is_expired():
            pending.delete()
            messages.error(request, "OTP has expired.")
            return redirect("home")

        user = User(
            username=pending.email,
            email=pending.email,
            first_name=pending.first_name,
            last_name=pending.last_name,
        )

        # Password is already hashed in PendingRegistration
        user.password = pending.password
        user.save()

        Profile.objects.create(
            user=user,
            phone=pending.phone,
        )

        login(request, user)

        pending.delete()

        messages.success(request, "Account verified successfully!")
        request.session.pop("pending_email", None)
        return redirect("dashboard")

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

        if not phone.isdigit():
            messages.error(request, "Phone number must contain only numbers.")
            return redirect("home")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("home")

        if Profile.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already registered.")
            return redirect("home")

        otp = generate_otp()

        # Remove any previous pending registration
        PendingRegistration.objects.filter(email=email).delete()

        PendingRegistration.objects.create(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            password=make_password(password),
            otp=otp,
        )

        send_brevo_email(
            email,
            "Verify your account",
            f"<h2>Your verification code is <b>{otp}</b></h2>",
        )
        request.session["pending_email"] = email

        messages.success(request, "Verification code sent to your email.")

        return redirect("verify_otp")

    return redirect("home")


def forgot_password(request):

    if request.method == "POST":
        email = request.POST.get("email")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "No account exists with that email.")
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

            <p>Click the button below.</p>

            <p>
                <a href="{reset_link}">
                    Reset Password
                </a>
            </p>

            <p>
                If you didn't request this,
                ignore this email.
            </p>
            """,
        )

        print(response.status_code)
        print(response.text)

        messages.success(request, "A password reset link has been sent.")

        return redirect("forgot_password")

    return render(request, "forgot_password.html")


def reset_password(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

    except Exception:
        user = None

    if not user:
        return render(request, "reset_invalid.html")

    if not default_token_generator.check_token(user, token):
        return render(request, "reset_invalid.html")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html")

        user.set_password(password)
        user.save()

        messages.success(request, "Password updated successfully.")

        return redirect("login")

    return render(request, "reset_password.html")


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
    return render(request, "categories.html", {"categories": categories})
