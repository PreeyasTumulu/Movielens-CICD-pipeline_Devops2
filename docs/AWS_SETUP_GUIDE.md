# AWS + Jenkins Setup Guide (click-by-click)

This is the implementation manual. **Take a screenshot at every 📸 marker** —
those map directly to the report sections and the marks. Region used
throughout: **Asia Pacific (Mumbai) `ap-south-1`**. Use **free-tier** sizes.

> Order matters: build the **VPC first**, then S3 + IAM, then EC2 (which launches
> into the VPC), then Jenkins, then wire up the pipeline.

---

## Phase A — Custom VPC networking  (6 marks)

### A1. Create the VPC
1. AWS Console → **VPC** → *Your VPCs* → **Create VPC**.
2. Choose **VPC only**. Name: `cicd-vpc`. IPv4 CIDR: `10.0.0.0/16`. Create.
   📸 `01_vpc_created.png`

### A2. Create a public subnet
1. **Subnets** → **Create subnet** → select `cicd-vpc`.
2. Name: `cicd-public-subnet`. AZ: `ap-south-1a`. CIDR: `10.0.1.0/24`. Create.
3. Select the subnet → **Actions → Edit subnet settings** → enable
   **Auto-assign public IPv4**. Save.
   📸 `02_public_subnet.png`

### A3. Internet Gateway
1. **Internet gateways** → **Create** → name `cicd-igw` → Create.
2. Select it → **Actions → Attach to VPC** → choose `cicd-vpc`.
   📸 `03_igw_attached.png`

### A4. Route table
1. **Route tables** → **Create** → name `cicd-public-rt`, VPC `cicd-vpc`.
2. Select it → **Routes → Edit routes → Add route**:
   Destination `0.0.0.0/0` → Target **Internet Gateway → `cicd-igw`**. Save.
3. **Subnet associations → Edit → associate `cicd-public-subnet`**. Save.
   📸 `04_route_table.png`

### A5. Connectivity verification (do after EC2 exists)
From your machine: `ping <ec2-public-ip>` or `ssh ...` succeeding proves the
IGW + route table work. 📸 `05_connectivity_test.png`

---

## Phase B — S3 dataset  (5 marks)

### B1. Create the bucket
1. **S3** → **Create bucket**. Name (globally unique): `movielens-cicd-dataset-<yourname>`.
   Region `ap-south-1`. Keep **Block all public access ON** (we use an IAM role,
   not public access). Create. 📸 `06_s3_bucket_created.png`

### B2. Upload the dataset
1. Download the dataset (already bundled at `app/data/u.user`, or):
   `curl -O https://raw.githubusercontent.com/justmarkham/DAT8/master/data/u.user`
2. Open the bucket → **Upload** → add `u.user` → Upload.
   📸 `07_dataset_uploaded.png`  (show the object key = `u.user`)

### B3. IAM role for EC2 → S3 read  (secure, no keys)
1. **IAM → Policies → Create policy → JSON tab**. Paste `deploy/s3-read-policy.json`,
   replacing the bucket name. Name it `MovieLensS3Read`. Create.
2. **IAM → Roles → Create role** → trusted entity **AWS service → EC2**.
   Attach `MovieLensS3Read`. Name: `MovieLensEC2Role`. Create.
   📸 `08_iam_role.png`
   *(You'll attach this role to the App EC2 in Phase C.)*

---

## Phase C — EC2 instances  (8 marks)

We launch **two** instances into `cicd-public-subnet`: **EC2 #1 = Jenkins**,
**EC2 #2 = App**.

### C1. Security groups
Create two SGs in `cicd-vpc` (**EC2 → Security Groups → Create**):
- `jenkins-sg` — inbound: SSH `22` (My IP), Custom TCP `8080` (My IP).
- `app-sg` — inbound: SSH `22` (My IP), Custom TCP `5000` (0.0.0.0/0 to demo the
  app publicly), and SSH `22` **from `jenkins-sg`** (so Jenkins can deploy).
  📸 `09_security_groups.png`

### C2. Launch EC2 #1 — Jenkins
1. **EC2 → Launch instance**. Name `jenkins-server`.
   AMI **Ubuntu 22.04 LTS**, type **t2.micro**.
2. Key pair: create/download `cicd-key.pem`.
3. **Network settings → Edit**: VPC `cicd-vpc`, Subnet `cicd-public-subnet`,
   Auto-assign public IP **Enable**, Security group **jenkins-sg**.
4. Launch. 📸 `10_jenkins_ec2.png`

### C3. Launch EC2 #2 — App
Same as above but: Name `app-server`, Security group **app-sg**, and under
**Advanced details → IAM instance profile** choose **`MovieLensEC2Role`**.
Launch. Note its **private IP** (e.g. `10.0.1.20`) — Jenkins deploys to it.
📸 `11_app_ec2.png`  (and 📸 the IAM role shown on the instance)

### C4. Prepare the App server (SSH in)
```bash
ssh -i cicd-key.pem ubuntu@<app-public-ip>
# python3-pandas/python3-numpy are prebuilt (avoids a memory-heavy source
# compile that OOMs t2.micro on Ubuntu 26.04 / Python 3.14):
sudo apt update && sudo apt install -y python3-venv python3-pip rsync git python3-pandas python3-numpy
# verify the IAM role works (no keys needed):
aws sts get-caller-identity 2>/dev/null || sudo snap install aws-cli --classic
sudo mkdir -p /opt/movielens && sudo chown -R ubuntu:ubuntu /opt/movielens
```
The systemd service is installed automatically by the first deploy, or manually:
`sudo cp deploy/movielens.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable movielens`
(Edit `S3_BUCKET` in that file to your bucket name first.)

---

## Phase D — Jenkins CI/CD  (10 marks — the big one)

### D1. Install Jenkins on EC2 #1
```bash
ssh -i cicd-key.pem ubuntu@<jenkins-public-ip>
sudo apt update && sudo apt install -y openjdk-17-jdk python3-venv python3-pip rsync python3-pandas python3-numpy
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/" | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update && sudo apt install -y jenkins
sudo systemctl enable --now jenkins
```
Open `http://<jenkins-public-ip>:8080`. Unlock with
`sudo cat /var/lib/jenkins/secrets/initialAdminPassword`. Install **suggested
plugins**, create the admin user.
📸 `12_jenkins_install.png`  `13_jenkins_unlock.png`

Also install these plugins (**Manage Jenkins → Plugins**): **GitHub**,
**Pipeline**, **SSH Agent**, **JUnit**. 📸 `14_jenkins_plugins.png`

### D2. Give Jenkins the SSH key to reach the App server
1. **Manage Jenkins → Credentials → (global) → Add Credentials**.
2. Kind **SSH Username with private key**. ID: **`app-server-ssh`** (must match
   the Jenkinsfile). Username `ubuntu`. Paste the contents of `cicd-key.pem`. Save.
   📸 `15_jenkins_ssh_cred.png`
3. On the Jenkins server, let the `jenkins` user reach the app host once to seed
   known_hosts is optional — the Jenkinsfile uses `StrictHostKeyChecking=no`.

### D3. Create the Pipeline job
1. **New Item → Pipeline**. Name `movielens-cicd`.
2. **Build Triggers → ✔ GitHub hook trigger for GITScm polling.**
3. **Pipeline → Definition: Pipeline script from SCM**. SCM **Git**, repo URL
   `https://github.com/<you>/<repo>.git`, branch `*/main`, Script Path
   `Jenkinsfile`. Save. 📸 `16_pipeline_job_config.png`
4. **Edit the Jenkinsfile** `environment` block: set `APP_SERVER` to EC2 #2's
   **private IP**, and `APP_USER=ubuntu`. Commit & push.

### D4. Connect GitHub → Jenkins (webhook = auto-trigger)
1. GitHub repo → **Settings → Webhooks → Add webhook**.
2. Payload URL: `http://<jenkins-public-ip>:8080/github-webhook/`.
   Content type `application/json`. Event: **Just the push event**. Add.
   📸 `17_github_webhook.png`  (show the green ✔ "recent delivery")

### D5. Run it
- First run: **Build Now** to confirm Build/Test/Deploy all go green.
- **Then prove automation**: make a small commit (e.g. edit README), `git push`,
  and watch Jenkins start a build **on its own**.
  📸 `18_pipeline_stages_green.png` (Stage View: Build→Test→Deploy)
  📸 `19_build_log.png`  📸 `20_test_log.png` (pytest 9 passed)  📸 `21_deploy_log.png`
  📸 `22_auto_triggered_build.png` (build started "by GitHub push")

---

## Phase E — Verify the live app  (4 marks)
1. Browser → `http://<app-public-ip>:5000` → dashboard loads.
   📸 `23_app_running.png`
2. Confirm it's reading from S3: the badge says *"Data source: AWS S3"* and
   `http://<app-public-ip>:5000/health` shows the S3 source.
   📸 `24_app_health_s3.png`

---

## Teardown (avoid charges)
**Stop** (not terminate) EC2 when not demoing; **terminate** both EC2, delete the
NAT-free VPC, S3 bucket, and IAM role after submission. S3 + t2.micro are free
tier but don't leave instances running for weeks.

## Screenshot checklist (24 shots → maps to report)
A: 01–05 · B: 06–08 · C: 09–11 · D: 12–22 · E: 23–24
