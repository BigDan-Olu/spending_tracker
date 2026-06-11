from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path(
        "categories/",
        views.categories,
        name="categories",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="password_reset.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "transactions/edit/<int:id>/",
        views.edit_transaction,
        name="edit_transaction",
    ),
    path(
        "transactions/delete/<int:id>/",
        views.delete_transaction,
        name="delete_transaction",
    ),
    path(
        "register/",
        views.register_user,
        name="register_user",
    ),
    path(
        "spending/add/",
        views.add_spending,
        name="add_spending",
    ),
    path(
        "transactions/",
        views.transaction_log,
        name="transaction_log",
    ),
]
