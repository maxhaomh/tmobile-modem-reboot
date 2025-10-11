# T-Mobile Modem Auto-Reboot Script

A lightweight Python script designed to automatically log in and restart a T-Mobile 5G Home Internet gateway. This is
useful for scheduling regular reboots to maintain a stable internet connection.

## Why Use This?

Some users of the T-Mobile Home Internet service find that the modem/gateway can become slow or lose connectivity over
time, requiring a manual reboot to fix. This script automates that process, which is especially helpful if you are
running a home server or other services that rely on a consistent internet connection.

## Prerequisites

- Python 3
- The `requests` library for Python

## Installation & Setup

1. Clone the repository or download the script.
2. Install the required Python library:

    ```bash
    pip3 install requests
    ```

3. Configure Your Password (Recommended: Use an Environment Variable):

    ```bash
    export MODEM_PASSWORD="your_modem_admin_password"
    ```

   To make this setting permanent across reboots, add this line to your `~/.bashrc` or `~/.profile` file.

## Usage

To run the script manually and reboot your modem immediately, execute:

```bash
python3 reboot_modem.py
```

## Automating with Cron

You can schedule the script to run at regular intervals using a cron job. For example, to reboot the modem every day at
4:00 AM:

1. Open your crontab file for editing:

    ```bash
    crontab -e
    ```

2. Add the following line to the file, making sure to use the absolute paths to your Python interpreter and script:

    ```bash
    0 4 * * * /usr/bin/python3 /home/pi/path/to/reboot_modem.py
    ```

3. Save and close the editor. The script will now run automatically on the schedule you defined.
