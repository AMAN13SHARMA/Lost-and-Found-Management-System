"""
AuthViews (Class Diagram 1).

+register_view(request) : HttpResponse    FR-01, FR-05 (and auto-login, SRS 4.1.2 step 4)
+login_view(request)    : HttpResponse    FR-02, FR-05
+logout_view(request)   : HttpResponse    FR-03 (POST only - NFR-09)
+redirect_to_login(request)               UI-02 - provided by LOGIN_URL + @login_required
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import redirect_to_login as django_redirect_to_login
from django.shortcuts import redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, RegistrationForm


def _safe_next(request):
    """Return the ?next= target only if it is a safe, local URL."""
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(
        nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return nxt
    return None


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Session.create(user): log the newly registered user in.
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect(_safe_next(request) or "dashboard:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form, "next": _safe_next(request) or ""})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Session.create(user)
            messages.success(request, f"Signed in as {user.username}.")
            return redirect(_safe_next(request) or resolve_url(settings.LOGIN_REDIRECT_URL))
        messages.error(request, "Login failed. Please check your credentials.")
    else:
        form = LoginForm(request)
    return render(request, "accounts/login.html", {"form": form, "next": _safe_next(request) or "", "google_login_enabled": settings.GOOGLE_LOGIN_ENABLED})


@require_POST
def logout_view(request):
    logout(request)  # Session.destroy()
    messages.info(request, "You have been logged out.")
    return redirect(settings.LOGOUT_REDIRECT_URL)


def redirect_to_login(request):
    """UI-02: send an anonymous visitor to the login page, preserving ?next=."""
    return django_redirect_to_login(request.get_full_path(), resolve_url(settings.LOGIN_URL))
