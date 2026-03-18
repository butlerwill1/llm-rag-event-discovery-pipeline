# Quick Start: Email Setup (5 Minutes)

Follow these steps to get email notifications working.

## Step 1: Install boto3 (30 seconds)

```bash
pip install boto3
```

## Step 2: Create Bot Gmail (2 minutes)

1. Go to https://gmail.com
2. Click "Create account"
3. Create: `london-events-bot@gmail.com` (or similar)
4. Save the password

## Step 3: Update .env File (30 seconds)

Edit your `.env` file:

```bash
# Your existing OpenAI key
OPENAI_API_KEY=sk-proj-...

# Add these new lines
AWS_REGION=eu-west-1
SES_FROM_EMAIL=london-events-bot@gmail.com
SES_TO_EMAIL=butler.will1@gmail.com
```

## Step 4: Verify Emails in AWS SES (2 minutes)

### Option A: AWS Console (Recommended)

1. Go to: https://eu-west-1.console.aws.amazon.com/ses/home?region=eu-west-1#/verified-identities
2. Click **"Create identity"**
3. Select **"Email address"**
4. Enter: `london-events-bot@gmail.com`
5. Click **"Create identity"**
6. Check Gmail inbox → Click verification link
7. **Repeat steps 2-6** for `butler.will1@gmail.com`

### Option B: AWS CLI

```bash
# Verify both emails
aws ses verify-email-identity --email-address london-events-bot@gmail.com --region eu-west-1
aws ses verify-email-identity --email-address butler.will1@gmail.com --region eu-west-1

# Check your email inboxes and click the verification links
```

## Step 5: Test Email (30 seconds)

```bash
python email_service.py
```

**Expected output:**
```
Testing Email Service...
✅ Email sent successfully!
   Message ID: 0100018d...
   From: london-events-bot@gmail.com
   To: butler.will1@gmail.com
```

**Check your inbox** at `butler.will1@gmail.com` - you should see a test email!

## Step 6: Run Full System

```bash
python main.py
```

This will:
1. Search for events
2. Find new events
3. Send you an email digest

---

## Troubleshooting

### ❌ "Email address is not verified"

**Fix:** Go to SES console and verify both emails (check spam for verification emails)

### ❌ "AccessDenied" or "Credentials not found"

**Fix:** Configure AWS credentials:
```bash
aws configure
```

Enter your AWS Access Key ID and Secret Access Key.

### ❌ "SES_FROM_EMAIL environment variable is required"

**Fix:** Make sure your `.env` file has `SES_FROM_EMAIL=london-events-bot@gmail.com`

### ❌ Email goes to spam

**Fix:** 
- Mark as "Not Spam" in Gmail
- Future emails will go to inbox
- (Optional) Request SES production access for better deliverability

---

## What's Next?

Once email is working locally:

1. **S3 Integration** - Store events in S3 instead of local CSV
2. **Dockerize** - Package as Docker container
3. **Deploy to AWS** - Run on ECS Fargate
4. **Schedule** - EventBridge trigger every Sunday 9am

See `AWS_SES_SETUP.md` for detailed documentation.

---

## Quick Reference

**Test email only:**
```bash
python email_service.py
```

**Full event search + email:**
```bash
python main.py
```

**Check SES verified emails:**
```bash
aws ses list-verified-email-addresses --region eu-west-1
```

**Your email addresses:**
- **From:** london-events-bot@gmail.com (create this)
- **To:** butler.will1@gmail.com (your email)
