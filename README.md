# Lost and Found Management System — NITC

**Prepared for:** National Institute of Technology, Calicut (NITC) · Group 18  
**Specification:** Software Requirements Specification (SRS) Version 1.0 + Companion UML Class & Sequence Diagrams

A centralized web-based platform built with **Python, Django, SQLite, Pillow, HTML5, CSS3, and JavaScript** that enables NITC students, faculty members, staff, and administrators to report lost and found belongings, search and filter reports, submit and review ownership claims, track activity on a personal dashboard, and resolve recovered items.

---

## 1. Quick Start

```powershell
# 1. Navigate to the project folder
cd C:\Users\sachi\.gemini\antigravity\scratch\lost_found_nitc

# 2. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 3. Apply database migrations (SQLite)
python manage.py migrate

# 4. (Optional) Seed realistic NITC demo users, items, photos & claims
python manage.py seed_demo

# 5. Start the Django development server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser (Django Admin: **http://127.0.0.1:8000/admin/**).

### Demo Accounts (created by `python manage.py seed_demo`)

| Role (SRS 2.3) | Username | Password | Capabilities |
|---|---|---|---|
| **Administrator (Superuser)** | `admin` | `admin12345` | Full Django Admin access (`FR-34`, `FR-35`), staff claim/resolution privileges |
| **Authorized Staff** | `staff_security` | `nitc12345` | Central Library / Security Desk staff; can review claims & resolve reports (`FR-23`, `FR-31`) |
| **Faculty Member** | `prof_menon` | `nitc12345` | Report lost/found items, review claims on own reports, submit claims |
| **Student** | `aarav_b23cs` | `nitc12345` | Report lost/found items, submit claims, manage own reports & dashboard |
| **Student** | `diya_b22ec` | `nitc12345` | Has open found reports with pending claims ready for review |
| **Student** | `rohan_b24me` | `nitc12345` | Has submitted claims and lost item reports |

---

## 2. User Documentation (SRS Section 2.6)

### 2.1 Registration and Login Guide
1. Click **Register** in the top navigation bar to create a new campus account with your username, name, email address, and password (`FR-01`).
2. Upon valid registration, you are automatically signed in (`SRS 4.1.2`). Existing users can sign in at **Log in** (`FR-02`).
3. Click **Log out** in the header to end your authenticated session (`FR-03`).

### 2.2 Lost and Found Item Reporting Guide
1. Sign in and click **+ Report an Item** (`FR-04`, `FR-06`).
2. Choose **I lost something (`LOST`)** or **I found something (`FOUND`)** and enter the required details: **Title**, **Category**, **Description**, **Location**, **Date Lost/Found**, and **Contact Method** (`FR-07`).
3. Optionally specify a **Collection Point** and attach a **Photograph** (`JPEG`, `PNG`, or `WebP`, up to `5 MB`) (`FR-08`, `FR-09`, `NFR-03`).
4. Avoid including sensitive personal identifiers such as full ID/Aadhaar numbers (`NFR-04`). New reports start with status **`OPEN`** (`FR-10`).

### 2.3 Searching and Browsing Guide
1. Open **Browse Items** (`/items/`) to view all unresolved (`OPEN` and `CLAIM_PENDING`) reports (`FR-12`).
2. Enter a keyword to perform a **case-insensitive search** across **title, description, location, and category** (`FR-13`).
3. Filter by **Report Type (`LOST` / `FOUND`)**, **Category**, and **Location** (`FR-14`, `FR-15`).
4. Click any item card to open the **Item Detail Page** (`FR-16`).

### 2.4 Claim Submission & Review Guide
1. Open the detail page of an item you believe belongs to you and enter a detailed **Ownership Explanation** (`FR-17`).
2. The system verifies that you are logged in (`BR-01`), not claiming your own report (`FR-18`, `BR-02`), the item is not `RESOLVED` (`FR-19`), and you have not already claimed the item (`FR-20`, `BR-03`, `NFR-15`).
3. Valid claims are saved as **`PENDING`** and the item status updates to **`CLAIM_PENDING`** (`FR-21`, `FR-22`).
4. The report creator (or authorized staff) reviews received claims on the item page or dashboard and clicks **Approve** or **Reject** (`FR-23`..`FR-26`, `BR-04`, `BR-05`).
5. **Important (`BR-06`, `NFR-05`, `NFR-06`):** Approving a claim does *not* automatically resolve the item or serve as proof of ownership. Users coordinate the physical handover at a safe campus location.

### 2.5 Dashboard and Status Management Guide
1. Open **Dashboard** (`/dashboard/`) to see your three live activity counts (`FR-27`..`FR-29`):
   - Total item reports you created
   - Pending claims received on your reports
   - Claim requests you submitted
2. Open **My Items** (`/my-items/`) to view all reports you created (including `RESOLVED`) and all claims you submitted (`FR-30`).
3. Once physical handover is complete, click **Mark as Resolved** on your report (`FR-31`). Resolved items have their modification timestamp updated (`FR-33`) and are excluded from public listings (`FR-32`, `BR-07`).

### 2.6 Administrative Guide
1. Authorized administrators (`is_staff` / `is_superuser`) can open **Admin** (`/admin/`) (`FR-34`, `FR-35`).
2. Manage `User`, `Administrator`, `Item`, and `ClaimRequest` records, including bulk actions to approve/reject pending claims or mark items as resolved.

---

## 3. Architecture & UML Traceability

| UML Diagram | Implemented Module(s) | Classes & Methods |
|---|---|---|
| **Class Diagram 1: Registration & Authentication** | `accounts/` | `User`, `Administrator` (proxy model), `RegistrationForm` (`clean_password2`, `save`), `LoginForm` (`is_valid`, `get_user`), `AuthViews` (`register_view`, `login_view`, `logout_view`, `redirect_to_login`), Django `Session` |
| **Class Diagram 2: Lost & Found Item Management** | `items/` | `Item` (`mark_resolved`, `mark_claim_pending`, `is_resolved`, `is_owned_by`), `ReportType` (`LOST`, `FOUND`), `ItemStatus` (`OPEN`, `CLAIM_PENDING`, `RESOLVED`), `ItemForm` (`clean_photo`, `save`), `ItemViews` (`home_view`, `item_list_view`, `item_detail_view`, `create_item_view`, `mark_resolved_view`, `my_items_view`, `search_items`) |
| **Class Diagram 3: Claim Request Management** | `claims/`, `dashboard/` | `ClaimRequest` (`approve`, `reject`, `is_pending`, `is_duplicate`), `ClaimStatus` (`PENDING`, `APPROVED`, `REJECTED`), `ClaimForm` (`clean_message`, `save`), `ClaimViews` (`submit_claim_view`, `decide_claim_view`, `check_eligibility`, `can_decide`), `DashboardService` (`count_user_reports`, `count_pending_claims`, `count_submitted_claims`, `get_received_claims`) |

---

## 4. Running Automated Tests (`NFR-16`)

```powershell
.\venv\Scripts\python.exe manage.py test -v 2
```

## Google sign-in (optional)
Create a Web application OAuth client in Google Cloud Console, configure the consent screen and add test users if needed. Register the exact redirect URI `http://127.0.0.1:8000/accounts/google/login/callback/`. For a deployed HTTPS host use its corresponding callback URI.

PowerShell (from the project directory):
```powershell
pip install -r requirements.txt
$env:GOOGLE_CLIENT_ID = "your-client-id"
$env:GOOGLE_CLIENT_SECRET = "your-client-secret"
python manage.py migrate
python manage.py check
python manage.py runserver
```
Open the existing login page and select Continue with Google. Without credentials, normal login remains available and the Google button is hidden. Never commit credentials. Existing password accounts are not automatically linked by email; Google sign-in does not grant staff privileges. Use a persistent database and secure secret key for production; the existing Vercel temporary SQLite demo is not suitable for reliable OAuth sessions.
