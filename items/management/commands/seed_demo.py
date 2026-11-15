"""
Management command to seed realistic NITC Lost & Found demo data.

Creates:
- 4 User classes from SRS Section 2.3:
  1. Administrator (superuser): admin / admin12345
  2. Staff member (is_staff=True): staff_security / nitc12345
  3. Faculty member: prof_menon / nitc12345
  4. Students: aarav_b23cs, diya_b22ec, rohan_b24me / nitc12345
- Sample LOST and FOUND item reports across NITC campus locations
  with Pillow-generated item photographs (JPEG/PNG/WebP).
- Sample ClaimRequests in PENDING, APPROVED, and REJECTED states,
  plus items in OPEN, CLAIM_PENDING, and RESOLVED states.
"""
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from claims.models import ClaimRequest, ClaimStatus
from items.models import Item, ItemStatus, ReportType


def _make_sample_image(title: str, bg_color: tuple[int, int, int], fmt: str = "JPEG") -> ContentFile:
    """Generate a clean sample photograph using Pillow (SRS 2.4 / 3.3)."""
    img = Image.new("RGB", (640, 480), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Draw decorative frame and item card illustration
    draw.rectangle([28, 28, 612, 452], outline=(255, 255, 255), width=3)
    draw.rectangle([60, 150, 580, 330], fill=(255, 255, 255, 30), outline=(255, 255, 255), width=2)
    draw.text((85, 205), "NITC LOST & FOUND", fill=(255, 255, 255))
    draw.text((85, 240), title[:42], fill=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format=fmt, quality=88)
    ext = fmt.lower()
    if ext == "jpeg":
        ext = "jpg"
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in title.lower())[:30]
    return ContentFile(buf.getvalue(), name=f"{safe_name}.{ext}")


class Command(BaseCommand):
    help = "Populate the database with realistic NITC Lost & Found demo data."

    def handle(self, *args, **options):
        today = timezone.localdate()

        # 1. Users (SRS 2.3: Students, Faculty Members, Staff Members, Administrators)
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@nitc.ac.in",
                "first_name": "Campus",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin12345")
            admin_user.save()

        staff_user, created = User.objects.get_or_create(
            username="staff_security",
            defaults={
                "email": "security.desk@nitc.ac.in",
                "first_name": "Rajan",
                "last_name": "Nair (Security Staff)",
                "is_staff": True,
            },
        )
        if created:
            staff_user.set_password("nitc12345")
            staff_user.save()

        faculty_user, created = User.objects.get_or_create(
            username="prof_menon",
            defaults={
                "email": "suresh.menon@nitc.ac.in",
                "first_name": "Dr. Suresh",
                "last_name": "Menon",
            },
        )
        if created:
            faculty_user.set_password("nitc12345")
            faculty_user.save()

        student1, created = User.objects.get_or_create(
            username="aarav_b23cs",
            defaults={
                "email": "aarav_b230412cs@nitc.ac.in",
                "first_name": "Aarav",
                "last_name": "Sharma",
            },
        )
        if created:
            student1.set_password("nitc12345")
            student1.save()

        student2, created = User.objects.get_or_create(
            username="diya_b22ec",
            defaults={
                "email": "diya_b220198ec@nitc.ac.in",
                "first_name": "Diya",
                "last_name": "Krishnan",
            },
        )
        if created:
            student2.set_password("nitc12345")
            student2.save()

        student3, created = User.objects.get_or_create(
            username="rohan_b24me",
            defaults={
                "email": "rohan_b240305me@nitc.ac.in",
                "first_name": "Rohan",
                "last_name": "Verma",
            },
        )
        if created:
            student3.set_password("nitc12345")
            student3.save()

        # 2. Sample Item Reports
        sample_items = [
            {
                "title": "Casio fx-991EX ClassWiz Scientific Calculator",
                "report_type": ReportType.FOUND,
                "category": "Electronics",
                "description": (
                    "Found a black Casio fx-991EX ClassWiz scientific calculator on a desk in "
                    "ELHC Room 203 after the morning Engineering Mathematics lecture. Has a small "
                    "sticker on the back cover."
                ),
                "location": "Electrical Lecture Hall Complex (ELHC)",
                "date_lost_found": today - timedelta(days=1),
                "collection_point": "Department of CSE Front Office / Contact via email",
                "contact_method": "diya_b220198ec@nitc.ac.in",
                "created_by": student2,
                "color": (17, 148, 107),
                "fmt": "JPEG",
            },
            {
                "title": "Blue NITC Student ID Card Holder with Keychain",
                "report_type": ReportType.FOUND,
                "category": "ID Card",
                "description": (
                    "Found a blue lanyard and transparent card holder near the Central Library "
                    "issue counter. A brass hostel room key is attached to the ring. Please "
                    "mention your branch and key number to claim."
                ),
                "location": "Central Library",
                "date_lost_found": today - timedelta(days=2),
                "collection_point": "Central Library Security Desk",
                "contact_method": "security.desk@nitc.ac.in / Ext. 2201",
                "created_by": staff_user,
                "color": (29, 63, 143),
                "fmt": "PNG",
            },
            {
                "title": "Black Sony WH-CH520 Wireless Headphones",
                "report_type": ReportType.LOST,
                "category": "Electronics",
                "description": (
                    "Lost my matte black Sony on-ear wireless headphones somewhere between the "
                    "Central Computer Centre (CCC) and Main Canteen around 5:30 PM. Has a tiny "
                    "scuff mark on the left earcup."
                ),
                "location": "Central Computer Centre (CCC)",
                "date_lost_found": today - timedelta(days=1),
                "collection_point": "",
                "contact_method": "aarav_b230412cs@nitc.ac.in / MBH Block B",
                "created_by": student1,
                "color": (217, 72, 95),
                "fmt": "WEBP",
            },
            {
                "title": "Silver Milton Thermosteel Water Bottle (1 Litre)",
                "report_type": ReportType.FOUND,
                "category": "Water Bottle",
                "description": (
                    "Found a 1L silver steel bottle left on the bench outside New Lecture Hall "
                    "Complex (NLHC) Room 102. Has a Tathva sticker on the side."
                ),
                "location": "New Lecture Hall Complex (NLHC)",
                "date_lost_found": today - timedelta(days=3),
                "collection_point": "NLHC Caretaker Room",
                "contact_method": "suresh.menon@nitc.ac.in",
                "created_by": faculty_user,
                "color": (45, 95, 155),
                "fmt": "JPEG",
            },
            {
                "title": "Introduction to Algorithms (CLRS) 3rd Edition",
                "report_type": ReportType.LOST,
                "category": "Books & Notes",
                "description": (
                    "Left my paperback copy of CLRS (Introduction to Algorithms) along with a "
                    "spiral notebook of Design & Analysis of Algorithms notes at the Main Canteen."
                ),
                "location": "Main Canteen",
                "date_lost_found": today - timedelta(days=4),
                "collection_point": "",
                "contact_method": "rohan_b240305me@nitc.ac.in",
                "created_by": student3,
                "color": (183, 121, 31),
                "fmt": "JPEG",
            },
            {
                "title": "Bunch of 3 Keys with Red Ragam Tag",
                "report_type": ReportType.FOUND,
                "category": "Keys",
                "description": (
                    "Found a set of three keys (one Godrej padlock key and two cycle keys) on a "
                    "red Ragam keychain along the walkway near Aryabhatta Hall."
                ),
                "location": "Aryabhatta Hall",
                "date_lost_found": today - timedelta(days=2),
                "collection_point": "Main Gate Security Office",
                "contact_method": "aarav_b230412cs@nitc.ac.in",
                "created_by": student1,
                "color": (22, 120, 90),
                "fmt": "PNG",
            },
            {
                "title": "Brown Leather Bi-Fold Wallet",
                "report_type": ReportType.FOUND,
                "category": "Wallet & Purse",
                "description": (
                    "Found a brown leather wallet near the Indoor Stadium badminton court. "
                    "Already handed over after verifying contents with the owner."
                ),
                "location": "Indoor Stadium",
                "date_lost_found": today - timedelta(days=6),
                "collection_point": "Indoor Stadium Office",
                "contact_method": "diya_b220198ec@nitc.ac.in",
                "created_by": student2,
                "color": (90, 98, 115),
                "fmt": "JPEG",
            },
        ]

        created_items = {}
        for spec in sample_items:
            item, item_created = Item.objects.get_or_create(
                title=spec["title"],
                created_by=spec["created_by"],
                defaults={
                    "report_type": spec["report_type"],
                    "category": spec["category"],
                    "description": spec["description"],
                    "location": spec["location"],
                    "date_lost_found": spec["date_lost_found"],
                    "collection_point": spec["collection_point"],
                    "contact_method": spec["contact_method"],
                    "status": ItemStatus.OPEN,
                },
            )
            if item_created:
                photo_file = _make_sample_image(spec["title"], spec["color"], spec["fmt"])
                item.photo.save(photo_file.name, photo_file, save=True)
            created_items[spec["title"]] = item

        # 3. Sample Claims showing full lifecycle (PENDING, APPROVED, REJECTED, RESOLVED)
        calc_item = created_items["Casio fx-991EX ClassWiz Scientific Calculator"]
        claim1, c1_created = ClaimRequest.objects.get_or_create(
            item=calc_item,
            claimant=student1,
            defaults={
                "message": (
                    "This is my calculator! It has a small blue 'CS-B' sticker on the back cover "
                    "and my roll number scratched lightly inside the slide-on hard case."
                ),
                "status": ClaimStatus.PENDING,
            },
        )
        if c1_created:
            calc_item.mark_claim_pending()

        keys_item = created_items["Bunch of 3 Keys with Red Ragam Tag"]
        claim2, c2_created = ClaimRequest.objects.get_or_create(
            item=keys_item,
            claimant=student3,
            defaults={
                "message": (
                    "Those are my hostel room and cycle keys! The Godrej key has '412' stamped on "
                    "one side and the Ragam tag is from Ragam '25."
                ),
                "status": ClaimStatus.PENDING,
            },
        )
        if c2_created:
            keys_item.mark_claim_pending()

        bottle_item = created_items["Silver Milton Thermosteel Water Bottle (1 Litre)"]
        claim3, c3_created = ClaimRequest.objects.get_or_create(
            item=bottle_item,
            claimant=student2,
            defaults={
                "message": (
                    "I left my 1L Milton bottle outside NLHC 102 after the Signals lecture. "
                    "It has a Tathva '24 sticker near the base and a small dent on the cap."
                ),
                "status": ClaimStatus.PENDING,
            },
        )
        if c3_created:
            bottle_item.mark_claim_pending()
            claim3.approve()  # Approved but awaiting physical handover (BR-06)

        wallet_item = created_items["Brown Leather Bi-Fold Wallet"]
        claim4, c4_created = ClaimRequest.objects.get_or_create(
            item=wallet_item,
            claimant=student3,
            defaults={
                "message": (
                    "Thank you! It's a Titan brown bi-fold wallet containing my SBI debit card "
                    "ending in 4821 and bus ticket receipts."
                ),
                "status": ClaimStatus.PENDING,
            },
        )
        if c4_created:
            wallet_item.mark_claim_pending()
            claim4.approve()
        if not wallet_item.is_resolved():
            wallet_item.mark_resolved()  # Completed physical handover (FR-31, FR-32)

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded NITC Lost & Found demo data:\n"
                "  - Admin:   admin / admin12345\n"
                "  - Staff:   staff_security / nitc12345\n"
                "  - Faculty: prof_menon / nitc12345\n"
                "  - Student: aarav_b23cs / nitc12345 (also diya_b22ec, rohan_b24me)\n"
                f"  - Items:   {Item.objects.count()} ({Item.objects.unresolved().count()} unresolved, "
                f"{Item.objects.filter(status=ItemStatus.RESOLVED).count()} resolved)\n"
                f"  - Claims:  {ClaimRequest.objects.count()}"
            )
        )
