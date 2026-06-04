import os
import requests
import sys
import time
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# ==========================================
# CONFIGURATION
# ==========================================

MODEM_IP = "192.168.12.1"
MODEM_PASSWORD = os.getenv("MODEM_PASSWORD", "your_password_goes_here")

SMTP_SERVER = "10.10.1.14"
SMTP_PORT = 25
SENDER_NAME = "Gateway Monitor"  # <--- Added Sender Name
SENDER_EMAIL = os.getenv("EMAIL_SENDER", "router@e.maxhao.net")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "max@maxhao.org")

STATUS_URL = f"http://{MODEM_IP}/TMI/v1/gateway?get=all"

# FAST TIMING FOR DEBUG
INITIAL_WAIT_SECONDS = 5
MAX_RETRIES = 3
RETRY_DELAY = 2

LOG_BUFFER = []


def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    LOG_BUFFER.append(formatted_msg)


def send_email_report(subject, body):
    log(f"Connecting to SMTP server at {SMTP_SERVER}:{SMTP_PORT}...")
    msg = MIMEMultipart()
    msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.send_message(msg)
        log("SUCCESS: Email report sent successfully.")
    except Exception as e:
        log(f"ERROR: Failed to send email: {e}")


def reboot_modem_debug():
    log("--- Starting DEBUG modem sequence (No actual reboot) ---")

    log("DEBUG: Simulating successful login...")
    log("DEBUG: Simulating reboot command sent...")

    log(f"Waiting {INITIAL_WAIT_SECONDS} seconds (simulated restart)...")
    time.sleep(INITIAL_WAIT_SECONDS)

    log("Checking modem status...")
    try:
        response = requests.get(STATUS_URL, timeout=5)
        details = response.json()

        s5g = details.get('signal', {}).get('5g', {})
        report_body = (
                f"** DEBUG TEST REPORT **\n"
                f"REBOOT STATUS: SUCCESS (Simulated)\n\n"
                f"Active Bands: {s5g.get('bands')}\n"
                f"RSRP: {s5g.get('rsrp')} dBm\n\n"
                f"EXECUTION LOGS:\n" + "\n".join(LOG_BUFFER)
        )
        send_email_report("DEBUG: Modem Status Report", report_body)
    except Exception as e:
        log(f"Failed to get status: {e}")
        send_email_report("DEBUG: Failed", f"Error: {e}\n\n" + "\n".join(LOG_BUFFER))


if __name__ == "__main__":
    reboot_modem_debug()
