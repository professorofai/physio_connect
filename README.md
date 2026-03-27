Physio Connect 

A Flask-based healthcare platform for booking physiotherapy appointments.

## Features
- User Registration/Login
- Physiotherapist Profiles
- Appointment Booking

## Tech Stack
- Flask
- SQLite
- HTML/CSS

## Status
🚧 In Progress (30%)

## Email configuration
Set environment variables before running:

- EMAIL_HOST (defaults to smtp.gmail.com)
- EMAIL_PORT (defaults to 587)
- EMAIL_HOST_USER (your SMTP user, e.g. Gmail email)
- EMAIL_HOST_PASSWORD (your SMTP app password)
- EMAIL_FROM (optional, default is EMAIL_HOST_USER)

Example:

```bash
export EMAIL_HOST_USER='your@gmail.com'
export EMAIL_HOST_PASSWORD='your-app-password'
python3 app.py
```
