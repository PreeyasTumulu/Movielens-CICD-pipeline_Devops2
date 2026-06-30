# MovieLens User Analytics — Automated CI/CD Pipeline

End-term DevOps project: a data-driven Flask web app deployed through a fully
automated **GitHub → Jenkins → AWS EC2** pipeline, with the dataset served from
**AWS S3** and all infrastructure inside a **custom AWS VPC**.

> **Dataset:** MovieLens `u.user` (943 users) — `user_id | age | gender | occupation | zip_code`
> Source: https://raw.githubusercontent.com/justmarkham/DAT8/master/data/u.user

## What the app shows
- **Total number of users** (943)
- **Age distribution** (summary stats + bucketed histogram)
- **Users grouped by occupation** (21 occupations, most common first)
- Bonus: gender split — all rendered as a dark dashboard with Chart.js

## Architecture
```
Developer → GitHub ──webhook──► Jenkins (EC2 #1) ──SSH/rsync──► Flask App (EC2 #2)
                                                                     │ IAM role
                                                                     ▼
                                                               AWS S3 (u.user)
   Both EC2 inside: Custom VPC → Public Subnet → Internet Gateway → Route Table
```

## Project structure
| Path | Purpose |
|------|---------|
| `app/app.py` | Flask routes: `/`, `/api/stats`, `/health` |
| `app/data_analysis.py` | Loads data (S3 via IAM role, or local fallback) + the 3 analyses |
| `app/templates/index.html` | Chart.js dashboard |
| `app/data/u.user` | Bundled dataset (local-dev / test fallback) |
| `tests/test_analysis.py` | pytest suite (runs in Jenkins Test stage) |
| `Jenkinsfile` | Declarative pipeline: Build → Test → Deploy |
| `deploy/movielens.service` | systemd unit for the app on EC2 #2 |
| `deploy/s3-read-policy.json` | IAM policy granting read access to the S3 dataset |
| `docs/AWS_SETUP_GUIDE.md` | Click-by-click AWS + Jenkins setup (with screenshot checklist) |
| `docs/REPORT_TEMPLATE.md` | Skeleton for the submission PDF |

## Run locally
```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows; use .venv/bin/activate on Linux/Mac
pip install -r requirements.txt
pytest -v                          # all tests should pass
python app/app.py                  # open http://localhost:5000
```
Locally the app reads the bundled `app/data/u.user`. On EC2 it reads from S3 —
set `S3_BUCKET` (done in `deploy/movielens.service`) and it switches automatically.

## How the dataset source is chosen
`data_analysis.load_data()` reads from **S3 via the EC2 IAM role** when the
`S3_BUCKET` env var is set (production), otherwise falls back to the bundled
local file (dev + Jenkins tests). **No AWS access keys are ever stored in code.**
