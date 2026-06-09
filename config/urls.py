"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# tracker/views.py
# config/urls.py
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from tracker import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path(
    "categories/",
    views.categories,
    name="categories"
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
    path("register/", views.register_user, name="register_user"),
    path("spending/add/", views.add_spending, name="add_spending"),
    path("transactions/", views.transaction_log, name="transaction_log"),
]