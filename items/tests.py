"""
Comprehensive Automated Test Suite for the NITC Lost and Found Management System.

Traceability coverage:
- FR-01 .. FR-05, UI-02, NFR-07: User Registration, Authentication, Session & Access Control
- FR-06 .. FR-11, FR-09, NFR-03, NFR-11, UI-01: Lost & Found Item Reporting + Photo Validation
- FR-12 .. FR-16, FR-32, BR-07, NFR-02: Browse, Case-Insensitive Search, Filtering & Detail View
- FR-17 .. FR-26, BR-01 .. BR-06, NFR-08, NFR-09, NFR-15, UI-03: Claim Submission & Review Decisions
- FR-27 .. FR-30: Personal Dashboard (DashboardService) & My Items Page
- FR-31 .. FR-33: Item Resolution & Timestamp Updates
- FR-34 .. FR-35: Administrative Management (Django Admin & Administrator proxy model)
- NFR-16: Repeatable automated testing of home page, item filtering, anonymous restrictions,
          claim creation, and permission checks.
"""
from datetime import timedelta
from io import BytesIO
import time

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Administrator, is_authorized_staff
from claims.models import ClaimAlreadyReviewed, ClaimRequest, ClaimStatus
from dashboard.services import DashboardService
from items.models import Item, ItemStatus, ReportType


def make_test_image_bytes(fmt: str = "JPEG", size=(120, 90)) -> bytes:
    img = Image.new("RGB", size, color=(29, 63, 143))
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class AuthAndRegistrationTests(TestCase):
    """Covers Class Diagram 1, Sequence Diagram 1 (Part A), FR-01 .. FR-05, UI-02, NFR-07."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="student_nitc",
            email="student@nitc.ac.in",
            password="StrongPassword123!",
        )

    def test_fr01_new_user_registration_and_auto_login(self):
        """FR-01: Valid registration creates an account, hashes password (NFR-07), and logs in."""
        resp = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new_b23cs",
                "first_name": "Neha",
                "last_name": "Menon",
                "email": "neha_b23cs@nitc.ac.in",
                "password1": "CampusPass#2026",
                "password2": "CampusPass#2026",
            },
        )
        self.assertRedirects(resp, reverse("dashboard:dashboard"))
        created_user = User.objects.get(username="new_b23cs")
        self.assertTrue(created_user.check_password("CampusPass#2026"))
        self.assertNotEqual(created_user.password, "CampusPass#2026")  # NFR-07 hashed

    def test_fr05_registration_validation_errors(self):
        """FR-05 / UI-01: Invalid registration data returns validation errors and creates no user."""
        resp = self.client.post(
            reverse("accounts:register"),
            {
                "username": "bad_user",
                "email": "student@nitc.ac.in",  # duplicate email
                "password1": "123",
                "password2": "456",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="bad_user").exists())
        self.assertContains(resp, "An account with this email address already exists.")

    def test_fr02_fr03_login_and_logout_session_lifecycle(self):
        """FR-02, FR-03: Login establishes session; POST logout terminates session."""
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "student_nitc", "password": "StrongPassword123!"},
        )
        self.assertRedirects(resp, reverse("dashboard:dashboard"))
        self.assertIn("_auth_user_id", self.client.session)

        logout_resp = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(logout_resp, reverse("items:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_fr04_ui02_anonymous_users_redirected_to_login(self):
        """FR-04, UI-02, BR-01, NFR-16: Protected pages redirect anonymous users to login."""
        protected_urls = [
            reverse("items:create_item"),
            reverse("dashboard:dashboard"),
            reverse("items:my_items"),
        ]
        for url in protected_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse("accounts:login"), resp["Location"])


class ItemReportingAndValidationTests(TestCase):
    """Covers Class Diagram 2, Sequence Diagram 1 (Part B), FR-06 .. FR-11, NFR-03, NFR-11, UI-01."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="reporter", email="reporter@nitc.ac.in", password="Password123!"
        )
        self.client.force_login(self.user)

    def test_fr06_to_fr11_create_lost_and_found_reports_with_photo(self):
        """FR-06..FR-11: Create LOST and FOUND reports with valid photo, status OPEN, creator & timestamps."""
        photo = SimpleUploadedFile(
            "id_card.jpg", make_test_image_bytes("JPEG"), content_type="image/jpeg"
        )
        resp = self.client.post(
            reverse("items:create_item"),
            {
                "report_type": ReportType.FOUND,
                "title": "NITC Student ID Card",
                "category": "ID Card",
                "description": "Found outside Central Library main entrance.",
                "location": "Central Library",
                "date_lost_found": timezone.localdate().isoformat(),
                "contact_method": "reporter@nitc.ac.in",
                "collection_point": "Central Library Desk",
                "photo": photo,
            },
        )
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertRedirects(resp, item.get_absolute_url())
        self.assertEqual(item.created_by, self.user)         # FR-10
        self.assertEqual(item.status, ItemStatus.OPEN)       # FR-10
        self.assertIsNotNone(item.created_at)                # FR-11
        self.assertIsNotNone(item.updated_at)                # FR-11
        self.assertTrue(bool(item.photo.name))

    def test_fr09_nfr03_reject_oversized_photo_over_5mb(self):
        """FR-09 / NFR-03: Reject uploaded photographs exceeding 5 MB."""
        oversized_bytes = make_test_image_bytes("JPEG") + (b"\x00" * (5 * 1024 * 1024 + 1024))
        photo = SimpleUploadedFile("huge.jpg", oversized_bytes, content_type="image/jpeg")
        resp = self.client.post(
            reverse("items:create_item"),
            {
                "report_type": ReportType.LOST,
                "title": "Lost Calculator",
                "category": "Electronics",
                "description": "Black scientific calculator lost in ELHC.",
                "location": "ELHC",
                "date_lost_found": timezone.localdate().isoformat(),
                "contact_method": "reporter@nitc.ac.in",
                "photo": photo,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Item.objects.count(), 0)
        self.assertContains(resp, "too large")

    def test_fr09_nfr11_reject_disallowed_mime_type(self):
        """FR-09 / NFR-11: Reject uploaded files with content type other than JPEG, PNG or WebP."""
        gif_bytes = make_test_image_bytes("GIF")
        bad_file = SimpleUploadedFile("anim.gif", gif_bytes, content_type="image/gif")
        resp = self.client.post(
            reverse("items:create_item"),
            {
                "report_type": ReportType.LOST,
                "title": "Lost Umbrella",
                "category": "Accessories",
                "description": "Blue folding umbrella left in Main Building.",
                "location": "Main Building",
                "date_lost_found": timezone.localdate().isoformat(),
                "contact_method": "reporter@nitc.ac.in",
                "photo": bad_file,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Item.objects.count(), 0)


class BrowseSearchFilterAndResolutionTests(TestCase):
    """Covers Class Diagram 2, Sequence Diagram 1 (Part C), FR-12 .. FR-16, FR-31 .. FR-33, BR-07, NFR-02."""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="Password123!")
        self.bob = User.objects.create_user(username="bob", password="Password123!")
        self.staff = User.objects.create_user(
            username="staff_member", password="Password123!", is_staff=True
        )
        today = timezone.localdate()

        self.open_lost = Item.objects.create(
            title="Black HP Laptop Charger",
            report_type=ReportType.LOST,
            category="Laptop & Accessories",
            description="65W USB-C charger lost near NLHC Room 104",
            location="New Lecture Hall Complex (NLHC)",
            date_lost_found=today,
            contact_method="alice@nitc.ac.in",
            created_by=self.alice,
            status=ItemStatus.OPEN,
        )
        self.open_found = Item.objects.create(
            title="Casio Calculator",
            report_type=ReportType.FOUND,
            category="Electronics",
            description="Found scientific calculator on bench in Central Library",
            location="Central Library",
            date_lost_found=today - timedelta(days=1),
            contact_method="bob@nitc.ac.in",
            created_by=self.bob,
            status=ItemStatus.OPEN,
        )
        self.resolved_item = Item.objects.create(
            title="Returned Hostel Keys",
            report_type=ReportType.FOUND,
            category="Keys",
            description="Already returned to owner at MBH",
            location="Mega Boys Hostel (MBH)",
            date_lost_found=today - timedelta(days=3),
            contact_method="bob@nitc.ac.in",
            created_by=self.bob,
            status=ItemStatus.RESOLVED,
        )

    def test_fr12_fr32_br07_home_and_listing_exclude_resolved_reports(self):
        """FR-12, FR-32, BR-07: Resolved reports are hidden from home page and ordinary item listing."""
        home_resp = self.client.get(reverse("items:home"))
        self.assertEqual(home_resp.status_code, 200)
        self.assertContains(home_resp, self.open_lost.title)
        self.assertContains(home_resp, self.open_found.title)
        self.assertNotContains(home_resp, self.resolved_item.title)

        list_resp = self.client.get(reverse("items:item_list"))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, self.open_lost.title)
        self.assertContains(list_resp, self.open_found.title)
        self.assertNotContains(list_resp, self.resolved_item.title)

    def test_fr13_fr14_fr15_keyword_search_and_filters(self):
        """FR-13, FR-14, FR-15: Case-insensitive keyword search across title/desc/location/category + filters."""
        # Case-insensitive keyword search on description ("usb-c")
        r1 = self.client.get(reverse("items:item_list"), {"q": "usb-c"})
        self.assertContains(r1, self.open_lost.title)
        self.assertNotContains(r1, self.open_found.title)

        # Filter by report_type=FOUND (FR-14)
        r2 = self.client.get(reverse("items:item_list"), {"type": "FOUND"})
        self.assertContains(r2, self.open_found.title)
        self.assertNotContains(r2, self.open_lost.title)

        # Filter by category & location (FR-15)
        r3 = self.client.get(
            reverse("items:item_list"),
            {"category": "Electronics", "location": "Central Library"},
        )
        self.assertContains(r3, self.open_found.title)
        self.assertNotContains(r3, self.open_lost.title)

    def test_fr16_item_detail_page(self):
        """FR-16: Detail page displays individual item report details."""
        resp = self.client.get(self.open_found.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.open_found.title)
        self.assertContains(resp, self.open_found.description)
        self.assertContains(resp, self.open_found.location)

    def test_fr31_fr33_only_creator_or_staff_can_mark_resolved_and_updates_timestamp(self):
        """FR-31, FR-33, BR-05, NFR-08: Only creator or staff can mark RESOLVED; updated_at is refreshed."""
        # Non-owner student cannot resolve Bob's item
        self.client.force_login(self.alice)
        self.client.post(reverse("items:mark_resolved", args=[self.open_found.pk]))
        self.open_found.refresh_from_db()
        self.assertEqual(self.open_found.status, ItemStatus.OPEN)

        # Creator (Bob) can resolve
        old_updated = self.open_found.updated_at
        self.client.force_login(self.bob)
        self.client.post(reverse("items:mark_resolved", args=[self.open_found.pk]))
        self.open_found.refresh_from_db()
        self.assertEqual(self.open_found.status, ItemStatus.RESOLVED)
        self.assertGreaterEqual(self.open_found.updated_at, old_updated)

        # Staff can also resolve Alice's item (FR-31)
        self.client.force_login(self.staff)
        self.client.post(reverse("items:mark_resolved", args=[self.open_lost.pk]))
        self.open_lost.refresh_from_db()
        self.assertEqual(self.open_lost.status, ItemStatus.RESOLVED)

    def test_nfr02_performance_1000_reports_search_under_3_seconds(self):
        """NFR-02: Search & filter on a dataset of 1,000 reports completes well within 3 seconds."""
        today = timezone.localdate()
        bulk_items = [
            Item(
                title=f"Campus Item #{i}",
                report_type=ReportType.FOUND if i % 2 == 0 else ReportType.LOST,
                category="Electronics" if i % 3 == 0 else "Books & Notes",
                description=f"Detailed description for item {i} near ELHC",
                location="Central Library" if i % 4 == 0 else "Main Canteen",
                date_lost_found=today,
                contact_method="user@nitc.ac.in",
                created_by=self.alice,
                status=ItemStatus.OPEN,
            )
            for i in range(1000)
        ]
        Item.objects.bulk_create(bulk_items)

        start = time.perf_counter()
        resp = self.client.get(
            reverse("items:item_list"),
            {"q": "ELHC", "type": "FOUND", "category": "Electronics"},
        )
        elapsed = time.perf_counter() - start
        self.assertEqual(resp.status_code, 200)
        self.assertLess(elapsed, 3.0)


class ClaimAndDashboardWorkflowTests(TestCase):
    """Covers Class Diagram 3, Sequence Diagrams 2 & 3, FR-17 .. FR-30, BR-01 .. BR-06, NFR-15."""

    def setUp(self):
        self.poster = User.objects.create_user(username="poster", password="Password123!")
        self.claimant = User.objects.create_user(username="claimant", password="Password123!")
        self.other = User.objects.create_user(username="other", password="Password123!")
        self.staff = User.objects.create_user(
            username="staff_reviewer", password="Password123!", is_staff=True
        )
        self.item = Item.objects.create(
            title="Found Casio fx-991EX Calculator",
            report_type=ReportType.FOUND,
            category="Electronics",
            description="Found in ELHC 203",
            location="ELHC",
            date_lost_found=timezone.localdate(),
            contact_method="poster@nitc.ac.in",
            created_by=self.poster,
            status=ItemStatus.OPEN,
        )

    def test_fr17_fr21_fr22_valid_claim_submission_sets_pending_and_claim_pending(self):
        """FR-17, FR-21, FR-22: Valid claim creates PENDING claim and moves item to CLAIM_PENDING."""
        self.client.force_login(self.claimant)
        resp = self.client.post(
            reverse("claims:submit_claim", args=[self.item.pk]),
            {
                "message": "It has my roll number B230412CS engraved on the back cover and a blue sticker."
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        claim = ClaimRequest.objects.get(item=self.item, claimant=self.claimant)
        self.assertEqual(claim.status, ClaimStatus.PENDING)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, ItemStatus.CLAIM_PENDING)
        self.assertContains(resp, "PENDING")

    def test_fr18_br02_cannot_claim_own_item(self):
        """FR-18, BR-02: Users cannot submit claims for their own item reports."""
        self.client.force_login(self.poster)
        self.client.post(
            reverse("claims:submit_claim", args=[self.item.pk]),
            {"message": "Trying to claim my own item report with a long explanation."},
        )
        self.assertEqual(ClaimRequest.objects.count(), 0)

    def test_fr19_cannot_claim_resolved_item(self):
        """FR-19: Prevent claim submission for reports already marked RESOLVED."""
        self.item.mark_resolved()
        self.client.force_login(self.claimant)
        self.client.post(
            reverse("claims:submit_claim", args=[self.item.pk]),
            {"message": "Trying to claim a resolved item report with enough characters."},
        )
        self.assertEqual(ClaimRequest.objects.count(), 0)

    def test_fr20_br03_nfr15_duplicate_claim_prevented_in_view_and_database(self):
        """FR-20, BR-03, NFR-15: Same claimant cannot submit more than one claim for the same item."""
        self.client.force_login(self.claimant)
        msg = "First valid claim explanation with identifying details on the item."
        self.client.post(reverse("claims:submit_claim", args=[self.item.pk]), {"message": msg})
        self.client.post(reverse("claims:submit_claim", args=[self.item.pk]), {"message": msg})
        self.assertEqual(ClaimRequest.objects.filter(item=self.item, claimant=self.claimant).count(), 1)

        # Also verify database UniqueConstraint directly (NFR-15)
        with self.assertRaises(IntegrityError):
            ClaimRequest.objects.create(item=self.item, claimant=self.claimant, message="Duplicate DB row")

    def test_fr23_to_fr26_br04_br05_br06_claim_review_and_permissions(self):
        """FR-23..FR-26, BR-04..BR-06: Only creator/staff can approve/reject; reviewed claims locked; item stays CLAIM_PENDING."""
        claim = ClaimRequest.objects.create(
            item=self.item,
            claimant=self.claimant,
            message="My calculator with B230412CS written inside the case.",
        )
        self.item.mark_claim_pending()

        # Unauthorized user cannot approve (FR-23, BR-05)
        self.client.force_login(self.other)
        self.client.post(reverse("claims:decide_claim", args=[claim.pk, "approve"]))
        claim.refresh_from_db()
        self.assertEqual(claim.status, ClaimStatus.PENDING)

        # Report creator approves (FR-23, FR-24)
        self.client.force_login(self.poster)
        self.client.post(reverse("claims:decide_claim", args=[claim.pk, "approve"]))
        claim.refresh_from_db()
        self.assertEqual(claim.status, ClaimStatus.APPROVED)

        # BR-06 / NFR-05: Approval does NOT automatically resolve the item report
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, ItemStatus.CLAIM_PENDING)

        # FR-25 / BR-04: Already reviewed claim cannot be processed again
        self.client.post(reverse("claims:decide_claim", args=[claim.pk, "reject"]))
        claim.refresh_from_db()
        self.assertEqual(claim.status, ClaimStatus.APPROVED)
        with self.assertRaises(ClaimAlreadyReviewed):
            claim.reject()

    def test_fr27_to_fr30_dashboard_counts_and_my_items_page(self):
        """FR-27..FR-30: DashboardService computes accurate counts and My Items lists reports & claims."""
        ClaimRequest.objects.create(
            item=self.item,
            claimant=self.claimant,
            message="Detailed ownership explanation for dashboard test.",
        )
        self.assertEqual(DashboardService.count_user_reports(self.poster), 1)       # FR-27
        self.assertEqual(DashboardService.count_pending_claims(self.poster), 1)     # FR-28
        self.assertEqual(DashboardService.count_submitted_claims(self.claimant), 1) # FR-29

        self.client.force_login(self.poster)
        dash_resp = self.client.get(reverse("dashboard:dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, self.item.title)

        my_items_resp = self.client.get(reverse("items:my_items"))
        self.assertEqual(my_items_resp.status_code, 200)
        self.assertContains(my_items_resp, self.item.title)

    def test_fr34_fr35_administrator_model_and_admin_access(self):
        """FR-34, FR-35: Django Admin restricted to staff/superuser; Administrator proxy model works."""
        self.assertTrue(is_authorized_staff(self.staff))
        self.assertFalse(is_authorized_staff(self.claimant))
        self.assertIn(self.staff, Administrator.objects.all())
        self.assertNotIn(self.claimant, Administrator.objects.all())

        # Non-staff user cannot access Django Admin (FR-35)
        self.client.force_login(self.claimant)
        resp_non_staff = self.client.get("/admin/")
        self.assertNotEqual(resp_non_staff.status_code, 200)

        # Staff user can access Django Admin login/index
        self.client.force_login(self.staff)
        resp_staff = self.client.get("/admin/")
        self.assertEqual(resp_staff.status_code, 200)
