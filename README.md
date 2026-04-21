Physio Connect

A Flask-based healthcare platform for booking physiotherapy appointments with phone verification.

## Features
- User Registration/Login with Phone OTP Verification
- Physiotherapist Profiles with Picture Upload
- Appointment Booking System
- Email Confirmations
- Modern Bootstrap UI

## Tech Stack
- Flask
- SQLite
- Bootstrap 5
- Twilio (SMS)
- HTML/CSS/JavaScript

## Status
✅ Complete - All features implemented

## Upcoming
- Building services model
- creating a Assitant bot

## Configuration

### 1. Twilio SMS Setup (Required for Phone Verification)
1. Sign up at [Twilio](https://www.twilio.com/)
2. Get your Account SID, Auth Token, and Phone Number
3. Set environment variables:

```bash
export TWILIO_ACCOUNT_SID='your_account_sid'
export TWILIO_AUTH_TOKEN='your_auth_token'
export TWILIO_PHONE_NUMBER='+1234567890'
```

### 2. Email Configuration (Optional)
Set environment variables for email confirmations:

```bash
export EMAIL_HOST='smtp.gmail.com'
export EMAIL_PORT='587'
export EMAIL_HOST_USER='your@gmail.com'
export EMAIL_HOST_PASSWORD='your-app-password'
export EMAIL_FROM='your@gmail.com'
```

### 3. Environment File
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## Installation & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (or use .env file)
source .env

# Run the application
python3 app.py
```

## Phone Number Format
Phone numbers must include country code:
- US: +1234567890
- India: +919876543210
- UK: +447123456789

## Security Features
- Phone number OTP verification for registration/login
- Password hashing with Werkzeug
- Session-based authentication
- File upload security with allowed extensions
