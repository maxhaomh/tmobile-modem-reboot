import os
from email.utils import formataddr

import requests
import sys
import time
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# CONFIGURATION
# ==========================================

MODEM_IP = "192.168.12.1"
# Ensure this is set in your environment variables
MODEM_PASSWORD = os.getenv("MODEM_PASSWORD", "your_password_goes_here")

# Email Settings
SMTP_SERVER = "10.10.1.14"
SMTP_PORT = 25
SENDER_NAME = "Gateway Monitor"  # <--- Added Sender Name
SENDER_EMAIL = os.getenv("EMAIL_SENDER", "router@e.maxhao.net")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "max@maxhao.org")

# API Endpoints
BASE_URL = f"http://{MODEM_IP}"
LOGIN_URL = f"{BASE_URL}/TMI/v1/auth/login"
REBOOT_URL = f"{BASE_URL}/TMI/v1/gateway/reset?set=reboot"
STATUS_URL = f"{BASE_URL}/TMI/v1/gateway?get=all"

# Timing Settings
INITIAL_WAIT_SECONDS = 180  # Wait 3 minutes for modem to reboot
MAX_RETRIES = 10  # Number of times to check status after wait
RETRY_DELAY = 30  # Seconds between status checks

# ==========================================
# LOGGING & UTILITIES
# ==========================================

LOG_BUFFER = []


def log(message):
    """Prints to console and appends to the log buffer for the email."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    LOG_BUFFER.append(formatted_msg)


def send_email_report(subject, body):
    """Sends an email via the local Postfix server."""
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


def check_connection_status():
    """Polls the modem status endpoint. Returns JSON dict or None."""
    try:
        response = requests.get(STATUS_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        return None
    return None


# ==========================================
# MAIN LOGIC
# ==========================================

def reboot_modem():
    if MODEM_PASSWORD == "your_password_goes_here":
        log("CRITICAL ERROR: Modem password not set.")
        sys.exit(1)

    log("--- Initiating Modem Reboot Sequence ---")
    session = requests.Session()
    auth_token = None

    # 1. Login
    try:
        log(f"Logging in to {MODEM_IP}...")
        login_payload = {"username": "admin", "password": MODEM_PASSWORD}
        response = session.post(LOGIN_URL, json=login_payload, timeout=10)
        response.raise_for_status()

        auth_token = response.json().get("auth", {}).get("token")
        if not auth_token:
            log("ERROR: Login failed (No token received).")
            sys.exit(1)
        log("Login successful.")

    except Exception as e:
        log(f"CRITICAL ERROR during login: {e}")
        sys.exit(1)

    # 2. Send Reboot Command
    try:
        log("Sending reboot command...")
        headers = {"Authorization": f"Bearer {auth_token}"}
        reboot_response = session.post(REBOOT_URL, headers=headers, timeout=10)
        reboot_response.raise_for_status()

        if reboot_response.status_code == 200:
            log("SUCCESS: Reboot command accepted by modem.")
        else:
            log(f"ERROR: Unexpected status code {reboot_response.status_code}")
            sys.exit(1)

    except Exception as e:
        log(f"CRITICAL ERROR during reboot command: {e}")
        sys.exit(1)

    # 3. Wait for Reboot
    log(f"Waiting {INITIAL_WAIT_SECONDS} seconds for hardware restart...")
    time.sleep(INITIAL_WAIT_SECONDS)

    # 4. Poll for Status
    log("Checking if modem is back online...")
    success = False
    details = {}

    for attempt in range(MAX_RETRIES):
        data = check_connection_status()
        if data:
            success = True
            details = data
            break
        log(f"Modem unreachable. Retrying in {RETRY_DELAY}s... ({attempt + 1}/{MAX_RETRIES})")
        time.sleep(RETRY_DELAY)

    # 5. Generate and Send Report
    if success:
        try:
            # -- Extract Data --
            device = details.get('device', {})
            signal = details.get('signal', {})
            s5g = signal.get('5g', {})
            s4g = signal.get('4g', {})
            gen = signal.get('generic', {})

            # Format Uptime
            uptime_sec = details.get('time', {}).get('upTime', 0)
            uptime_str = str(datetime.timedelta(seconds=uptime_sec))

            # Format Bands
            bands_5g = s5g.get('bands', [])
            bands_4g = s4g.get('bands', [])
            all_bands = bands_5g + bands_4g
            bands_str = ", ".join(all_bands) if all_bands else "None"

            # Execution Logs
            log("Status retrieved successfully. Generating report.")
            execution_logs = "\n".join(LOG_BUFFER)

            report_body = (
                f"Modem Reboot Report\n"
                f"==================================================\n"
                f"RESULT: SUCCESS\n"
                f"==================================================\n\n"

                f"NETWORK SUMMARY:\n"
                f"  - Status:       Online\n"
                f"  - Uptime:       {uptime_str}\n"
                f"  - APN:          {gen.get('apn', 'N/A')}\n"
                f"  - Connected Bands: {bands_str}\n\n"

                f"5G SIGNAL METRICS:\n"
                f"  - Bands: {bands_5g}\n"
                f"  - Bars:  {s5g.get('bars', 'N/A')}\n"
                f"  - RSRP:  {s5g.get('rsrp', 'N/A')} dBm\n"
                f"  - SINR:  {s5g.get('sinr', 'N/A')} dB\n"
                f"  - RSRQ:  {s5g.get('rsrq', 'N/A')} dB\n\n"

                f"4G SIGNAL METRICS:\n"
                f"  - Bands: {bands_4g}\n"
                f"  - Bars:  {s4g.get('bars', 'N/A')}\n"
                f"  - RSRP:  {s4g.get('rsrp', 'N/A')} dBm\n"
                f"  - SINR:  {s4g.get('sinr', 'N/A')} dB\n\n"

                f"DEVICE DETAILS:\n"
                f"  - Model:  {device.get('model', 'N/A')}\n"
                f"  - Serial: {device.get('serial', 'N/A')}\n"
                f"  - SW Ver: {device.get('softwareVersion', 'N/A')}\n\n"

                f"==================================================\n"
                f"SCRIPT EXECUTION LOGS\n"
                f"==================================================\n"
                f"{execution_logs}"
            )

            send_email_report("Modem Reboot Successful", report_body)

        except Exception as e:
            log(f"Error parsing JSON report: {e}")
            send_email_report("Modem Reboot Success (Parse Error)",
                              f"Modem is online but report generation failed.\n\nLogs:\n{LOG_BUFFER}")
    else:
        err_msg = "Modem reboot command was sent, but the device did not return online within the timeout period."
        log(err_msg)
        execution_logs = "\n".join(LOG_BUFFER)
        send_email_report("Modem Reboot Failed / Timed Out", f"{err_msg}\n\nLogs:\n{execution_logs}")


if __name__ == "__main__":
    reboot_modem()
