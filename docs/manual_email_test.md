# Manual Real Email Send Test

This test sends a real email using Gmail OAuth credentials. It is not part of automated pytest runs.

## Requirements
- `secrets/gmail_credentials.json` exists
- `.env` configured

## Run
PowerShell:
```
$env:REAL_EMAIL_TO="your_email@example.com"
$env:REAL_EMAIL_SUBJECT="AMIS Agent Test"
$env:REAL_EMAIL_BODY="This is a real send test."
python scripts/send_real_email.py
```

If successful, you will see a response containing an id.

