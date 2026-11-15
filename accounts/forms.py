"""
RegistrationForm and LoginForm (Class Diagram 1).

FR-01: register with valid registration information.
FR-02: authenticate with account credentials.
FR-05: display validation errors for invalid registration / login data.
NFR-07: passwords are handled by Django's password-management mechanisms.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class StyledFormMixin:
    """Adds the project's CSS class to every widget."""

    def _style_fields(self):
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()


class RegistrationForm(StyledFormMixin, UserCreationForm):
    """
    Attributes: username, email, password1, password2.
    Methods:    is_valid(), clean_password2() (inherited), save() -> User.
    """

    email = forms.EmailField(
        required=True,
        help_text="Used by other users to contact you about an item.",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@nitc.ac.in"}),
    )
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "e.g. b230123cs", "autofocus": True})
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)  # password hashed via set_password()
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    """
    Attributes: username, password.
    Methods:    is_valid(), get_user() -> User (inherited).
    """

    error_messages = {
        "invalid_login": "Please enter a correct username and password. Both fields are case-sensitive.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Username"})
        self.fields["password"].widget.attrs.update({"placeholder": "Password"})
        self._style_fields()
