"""
Class Diagram 1 - Registration and Authentication.

* ``User`` is Django's built-in authentication user model
  (``django.contrib.auth.models.User``). It already provides the attributes
  and methods shown in the class diagram: id, username, email, password
  (private, hashed), first_name, last_name, is_staff, is_superuser,
  date_joined, set_password(), check_password() and is_authenticated
  (FR-01, FR-02, NFR-07).

* ``Administrator`` specialises User through the ``is_staff`` /
  ``is_superuser`` flags (FR-34, FR-35). It is implemented as a *proxy*
  model so no extra table is created; it simply gives a typed view of the
  users that are allowed to access Django Admin.

* ``Session`` is Django's session framework (django.contrib.sessions).
"""
from django.contrib.auth.models import User, UserManager
from django.db import models
from django.db.models import Q


class AdministratorManager(UserManager):
    """Returns only users that hold staff or superuser permissions."""

    def get_queryset(self):
        return super().get_queryset().filter(Q(is_staff=True) | Q(is_superuser=True))


class Administrator(User):
    """A User with ``is_staff`` or ``is_superuser`` set (Class Diagram 1)."""

    objects = AdministratorManager()

    class Meta:
        proxy = True
        verbose_name = "administrator"
        verbose_name_plural = "administrators"

    # The methods below mirror the class diagram. Actual management is done
    # through the Django Admin site, whose access is controlled by Django's
    # staff / superuser permissions (FR-35).
    def can_access_admin_site(self) -> bool:
        return self.is_active and (self.is_staff or self.is_superuser)

    def can_manage_users(self) -> bool:
        return self.can_access_admin_site() and (
            self.is_superuser or self.has_perm("auth.change_user")
        )

    def can_manage_items(self) -> bool:
        return self.can_access_admin_site() and (
            self.is_superuser or self.has_perm("items.change_item")
        )

    def can_manage_claims(self) -> bool:
        return self.can_access_admin_site() and (
            self.is_superuser or self.has_perm("claims.change_claimrequest")
        )


def is_authorized_staff(user) -> bool:
    """
    "Authorized staff user" as used by FR-23, FR-31 and BR-05: an active
    authenticated user with Django's staff or superuser flag.
    """
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and (user.is_staff or user.is_superuser)
    )
