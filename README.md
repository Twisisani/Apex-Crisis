APEX-CRIS — National Crisis Intelligence, Response & Youth Empowerment Platform

APEX-CRIS is a secure, scalable, public-interest technology platform engineered for South Africa. It addresses three interconnected national challenges:

1. Graduate Unemployment and Youth Skills Development (Module 1)
2. Gender-Based Violence Prevention and Survivor Support (Module 2)
3. Drought, Agricultural Resilience and Food Security (Module 3)

Hosted on AWS Africa (af-south-1) infrastructure, the platform features a shared intelligence foundation, strict data-isolation boundaries, audit trails, and an end-to-end operational lifecycle.

---

Architectural Overview and Core Modules

* Citizen Portal: Secure registration, multi-module gadget suite (EMPLOYMENT, GBV_ALERT, EL_NINO_RELIEF), and a personal case-tracking journey center showing live stages, assigned partners, and next steps.
* Partner and Service Provider Portal: Verified organization management, referral acceptance, and service delivery confirmation.
* National Crisis Dispatch Command Center: Administrative command interface featuring live priority queues, status lifecycles (SUBMITTED -> UNDER REVIEW -> ASSIGNED -> ACKNOWLEDGED -> IN PROGRESS -> RESOLVED), audit logs, and reason tracking.
* Impact Analytics Dashboard: Outcome-based metrics tracking system-wide resolution rates, pillar distribution, and verified interventions.

---

Technology Stack

* Backend: Python 3.9+, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug
* Database: SQLite (local development) / Amazon RDS PostgreSQL (production)
* Frontend: Jinja2 Templates, Tailwind CSS (via CDN)
* Design Identity: Dark navy/slate palette (slate-950), emerald/blue interactive accents, and official humanitarian branding.
* Cloud and Containerization: Docker, Docker Compose, AWS SNS/SQS/RDS architecture for af-south-1.

---

Local Installation and Setup

1. Clone or Open the Repository
Open your terminal in the project directory:

```bash
git clone https://github.com/Twisisani/Apex-Crisis.git
cd Apex-Crisis

```

2. Create and Activate a Virtual Environment

```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate

```

3. Install Dependencies

```bash
pip install -r requirements.txt

```

4. Configure Environment Variables (Optional)
Create a .env file or export environment variables:

```bash
set SECRET_KEY=apex-enterprise-secure-key-2026
set DATABASE_URL=sqlite:///apex_cris.db

```

5. Run the Application

```bash
python app.py

```

Open your browser and navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

Default Administrator Access

To log into the Admin Command Center:

1. Navigate to [http://127.0.0.1:5000/admin/login](https://www.google.com/search?q=http://127.0.0.1:5000/admin/login).
2. Alternatively, register a new administrator account at /admin/register using the official system secret access code:
* Secret Access Code: APEX-SA-2026


3. Default pre-seeded system administrator credentials:
* Email: admin@apex.gov.za
* Password: Admin@2026



---

Operational Case Lifecycle

Every request submitted through the citizen gadget suite follows an auditable 6-stage lifecycle enforced by backend permissions:

1. SUBMITTED: Validated and securely persisted to the database.
2. UNDER REVIEW: Flagged for administrative triage.
3. ASSIGNED: Routed to a verified partner, employer, or responder.
4. ACKNOWLEDGED: Receiving team or NGO confirms receipt.
5. IN PROGRESS: Active intervention, counseling, or recruitment underway.
6. RESOLVED: Outcome verified and closed with full audit provenance.

---

Docker Deployment

To build and run the containerized application for AWS production:

```bash
docker-compose build
docker-compose up -d

```

---
