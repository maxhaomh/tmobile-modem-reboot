import os
import requests
import sys

MODEM_IP = "192.168.12.1"

MODEM_PASSWORD = os.getenv("MODEM_PASSWORD", "your_password_goes_here")

BASE_URL = f"http://{MODEM_IP}"
LOGIN_URL = f"{BASE_URL}/TMI/v1/auth/login"
REBOOT_URL = f"{BASE_URL}/TMI/v1/gateway/reset?set=reboot"


def reboot_modem():
    """
    Logs into the T-Mobile modem and sends the reboot command.
    """
    if MODEM_PASSWORD == "your_password_goes_here":
        print("ERROR: Please set your modem password in the script or as an environment variable.")
        sys.exit(1)

    print("--- Starting modem reboot sequence ---")
    session = requests.Session()
    auth_token = None
    try:
        print(f"Attempting to log in to {MODEM_IP}...")
        login_payload = {
            "username": "admin",
            "password": MODEM_PASSWORD
        }
        response = session.post(LOGIN_URL, json=login_payload, timeout=10)
        response.raise_for_status()  # This will raise an exception for HTTP errors (4xx or 5xx)

        login_data = response.json()
        auth_token = login_data.get("auth", {}).get("token")

        if not auth_token:
            print("ERROR: Could not retrieve auth token from login response.")
            sys.exit(1)

        print("Login successful. Auth token received.")

    except requests.exceptions.RequestException as e:
        print(f"ERROR during login: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        sys.exit(1)

    try:
        print("Sending reboot command...")
        headers = {
            "Authorization": f"Bearer {auth_token}"
        }
        reboot_response = session.post(REBOOT_URL, headers=headers, timeout=10)
        reboot_response.raise_for_status()

        if reboot_response.status_code == 200:
            print("SUCCESS: Reboot command sent successfully to the modem.")
            print("It may take a few minutes for the modem to restart.")
        else:
            print(f"ERROR: Received unexpected status code {reboot_response.status_code} on reboot command.")
            print(f"Response: {reboot_response.text}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR during reboot: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during reboot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    reboot_modem()
