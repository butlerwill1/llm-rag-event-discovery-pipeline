# AWS SES Setup Guide

This guide will walk you through setting up AWS SES (Simple Email Service) to send weekly event digest emails.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Gmail account for the bot (create a new one)

## Step 1: Create Bot Gmail Account

1. Go to https://accounts.google.com/signup
2. Create a new Gmail account (e.g., `london-events-bot@gmail.com`)
3. Save the credentials securely
4. This will be your `SES_FROM_EMAIL`

## Step 2: Configure AWS Credentials

If you haven't already, configure your AWS credentials:

```bash
aws configure
```

Enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `eu-west-1`
- Default output format: `json`

## Step 3: Verify Email Addresses in SES

### Via AWS Console (Easier)

1. Go to AWS Console: https://console.aws.amazon.com/ses/
2. Make sure you're in the **eu-west-1** region (check top-right corner)
3. Click **Verified identities** in the left sidebar
4. Click **Create identity**

**Verify the FROM email (bot email):**
5. Select **Email address**
6. Enter your bot email: `london-events-bot@gmail.com`
7. Click **Create identity**
8. Check the Gmail inbox and click the verification link
9. Wait for status to show "Verified"

**Verify the TO email (your personal email):**
10. Repeat steps 4-9 for `butler.will1@gmail.com`

### Via AWS CLI (Alternative)

```bash
# Verify FROM email
aws ses verify-email-identity --email-address london-events-bot@gmail.com --region eu-west-1

# Verify TO email
aws ses verify-email-identity --email-address butler.will1@gmail.com --region eu-west-1

# Check verification status
aws ses get-identity-verification-attributes \
  --identities london-events-bot@gmail.com butler.will1@gmail.com \
  --region eu-west-1
```

## Step 4: Update Environment Variables

Update your `.env` file:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-...

# AWS SES Email Configuration
AWS_REGION=eu-west-1
SES_FROM_EMAIL=london-events-bot@gmail.com
SES_TO_EMAIL=butler.will1@gmail.com
```

## Step 5: Install boto3

```bash
pip install boto3
```

## Step 6: Test Email Sending

Run the email service test:

```bash
python email_service.py
```

This will:
- Create sample test events
- Format them into text and HTML emails
- Send a test email via SES
- Print the plain text version to console

**Expected output:**
```
Testing Email Service...

--- Plain Text Email ---
Weekly Event Digest - January 19, 2026
...

--- Sending Test Email ---
✅ Email sent successfully!
   Message ID: 0100018d...
   From: london-events-bot@gmail.com
   To: butler.will1@gmail.com

✅ Test email sent successfully!
```

## Step 7: Check Your Inbox

Check `butler.will1@gmail.com` for the test email. It should have:
- Subject: "📅 Weekly Event Digest - 2 New Events - [Date]"
- Both plain text and HTML versions
- Sample events formatted nicely

## Troubleshooting

### Error: "Email address is not verified"

**Problem:** You're in SES Sandbox mode and haven't verified the email.

**Solution:**
1. Go to SES Console → Verified identities
2. Verify both sender and recipient emails
3. Check email inboxes for verification links

### Error: "AccessDenied"

**Problem:** Your AWS credentials don't have SES permissions.

**Solution:**
Add this policy to your IAM user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail",
        "ses:GetSendQuota"
      ],
      "Resource": "*"
    }
  ]
}
```

### Error: "MessageRejected"

**Problem:** Email content or configuration issue.

**Solution:**
- Check that FROM email is verified
- Check that TO email is verified (in sandbox mode)
- Ensure email content is valid

### Want to send to ANY email (not just verified)?

**Request Production Access:**

1. Go to SES Console
2. Click "Account dashboard"
3. Click "Request production access"
4. Fill out the form:
   - Mail type: Transactional
   - Use case: Personal event notification system
   - Compliance: Sending only to myself
5. Submit (usually approved in 24 hours)

## SES Sandbox vs Production

| Feature | Sandbox | Production |
|---------|---------|------------|
| Recipients | Only verified emails | Any email |
| Daily limit | 200 emails | 50,000 emails |
| Cost | Free | $0.10 per 1,000 emails |
| Setup | Immediate | 24hr approval |

For your weekly digest, **Sandbox mode is perfect** - you only need to send to yourself!

## Next Steps

Once email is working:
1. ✅ Test with `python email_service.py`
2. ✅ Test full workflow with `python main.py`
3. 🐳 Dockerize the application
4. ☁️ Deploy to AWS ECS Fargate
5. ⏰ Set up EventBridge schedule
