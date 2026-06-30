# Automated CI/CD Deployment Pipeline using GitHub, Jenkins & AWS
### DevOps2 End-Term Project Report

**Name:** _Preeyas Tumulu_  ·  **Roll No:** ______  ·  **Date:** ______
**Region:** AWS Asia Pacific (Mumbai) `ap-south-1`
**Repository:** https://github.com/______/______

> Fill each ⬚ placeholder with the matching screenshot from `screenshots/`.
> Export this file to PDF for submission (one PDF only).

---

## 1. Project Overview

**Problem statement.** Design, configure and implement a complete CI/CD pipeline
that automatically deploys a data-driven application — from code commit to running
on AWS — integrating GitHub, Jenkins, EC2, S3 and a custom VPC.

**Solution approach.** A Flask web app analyses the MovieLens `u.user` dataset
(943 users) stored in S3. Code lives in GitHub; every push fires a webhook that
triggers a Jenkins pipeline (Build → Test → Deploy). Jenkins runs on EC2 #1 and
deploys over SSH to the Flask app on EC2 #2. Both instances sit in a public
subnet of a custom VPC reached through an Internet Gateway. The app reads the
dataset from S3 using an **EC2 IAM role** — no credentials are stored anywhere.

**Technology stack.**
| Layer | Tool |
|-------|------|
| Source control | GitHub |
| CI/CD | Jenkins (declarative pipeline) |
| Compute | AWS EC2 (2× t2.micro, Ubuntu 22.04) |
| Storage | AWS S3 |
| Networking | AWS VPC, Subnet, IGW, Route Table |
| App | Python, Flask, pandas, gunicorn, Chart.js |
| Auth to S3 | AWS IAM role (instance profile) |
| Testing | pytest |

**System architecture diagram.**  ⬚ *(insert architecture diagram)*

---

## 2. AWS S3 Implementation Proof  *(5 marks)*
- ⬚ `06_s3_bucket_created.png` — bucket creation
- ⬚ `07_dataset_uploaded.png` — `u.user` uploaded (object key visible)
- ⬚ `08_iam_role.png` — IAM role/policy granting S3 read
- ⬚ `24_app_health_s3.png` — application reading the dataset from S3

**Observation:** access is granted via an IAM role attached to EC2 #2, so the app
authenticates to S3 with zero hard-coded keys.

---

## 3. GitHub Repository Documentation  *(part of 5 marks)*
- ⬚ Repository home page (files visible: `app/`, `Jenkinsfile`, `tests/`)
- ⬚ Commit history (multiple meaningful commits)
- ⬚ `17_github_webhook.png` — webhook → Jenkins integration (green delivery)

**Repo:** ______   **Commits:** ______

---

## 4. Jenkins CI/CD Documentation  *(10 marks)*
- ⬚ `12_jenkins_install.png` / `13_jenkins_unlock.png` — installation
- ⬚ `14_jenkins_plugins.png` — plugins (GitHub, Pipeline, SSH Agent, JUnit)
- ⬚ `15_jenkins_ssh_cred.png` — SSH credential `app-server-ssh`
- ⬚ `16_pipeline_job_config.png` — pipeline job (Pipeline-from-SCM + GitHub trigger)
- ⬚ `18_pipeline_stages_green.png` — Stage View: **Build → Test → Deploy** all green

**Pipeline execution proof (compulsory):**
- ⬚ `19_build_log.png` — Build stage (dependencies installed)
- ⬚ `20_test_log.png` — Test stage (**9 passed** in pytest)
- ⬚ `21_deploy_log.png` — Deploy stage (rsync + service restart + health check)
- ⬚ `22_auto_triggered_build.png` — build **auto-started by a GitHub push**

---

## 5. AWS EC2 Deployment Evidence  *(8 marks)*
- ⬚ `10_jenkins_ec2.png` — EC2 #1 (Jenkins) created
- ⬚ `11_app_ec2.png` — EC2 #2 (App) created, IAM role attached
- ⬚ `09_security_groups.png` — security-group rules (22 / 8080 / 5000)
- ⬚ `23_app_running.png` — application running (dashboard in browser)

---

## 6. AWS VPC Configuration Evidence  *(6 marks)*
- ⬚ `01_vpc_created.png` — custom VPC `10.0.0.0/16`
- ⬚ `02_public_subnet.png` — public subnet `10.0.1.0/24`
- ⬚ `03_igw_attached.png` — Internet Gateway attached
- ⬚ `04_route_table.png` — route `0.0.0.0/0 → IGW` + subnet association
- ⬚ `05_connectivity_test.png` — connectivity verification (ping/SSH)

---

## 7. Final Project Documentation  *(2 marks)*

**System architecture diagram.** ⬚ *(insert)*

**Application screenshots.** ⬚ dashboard · ⬚ `/api/stats` JSON · ⬚ `/health`

**Results & observations.**
- Total users: **943**  ·  Occupations: **21**  ·  Age range: **7–73** (mean 34.1)
- Top occupations: student (196), other (105), educator (95), administrator (79)
- Gender: M 670 / F 273
- Pipeline run time: ~____ s; auto-trigger latency after push: ~____ s

**Challenges faced & solutions.**
| Challenge | Solution |
|-----------|----------|
| Avoid storing AWS keys on EC2 | Used an IAM **role/instance profile** for S3 read |
| Jenkins → App auth for deploy | Stored SSH key as Jenkins credential; app-sg allows 22 from jenkins-sg |
| Parsing the `u.user` header row | `header=None` + `names=` + `skiprows=1` in pandas |
| App must survive reboots | Ran it as a **systemd** service with gunicorn |
| _add your own_ | _..._ |

**Conclusion.** A single `git push` now flows automatically through build, test
and deployment onto AWS infrastructure — demonstrating a complete, secure,
end-to-end CI/CD pipeline.
