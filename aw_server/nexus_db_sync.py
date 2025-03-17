import os
import re
import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

def export_all_data_to_remote_db(host, port):
    from .nexus_config import NEXUS_API_TOKEN, NEXUS_API_ENDPOINT

    logger.warning(f"Getting export data from {host}:{port}")
    app_url = f"http://{host}:{port}/api/0"

    export_data_response = requests.get(f"{app_url}/export")
    export_data = export_data_response.json()
    logger.warning("Export data received")

    info_data_response = requests.get(f"{app_url}/info")
    info_data = info_data_response.json()
    logger.warning(f"Info data received: {info_data}")
    payload = {"device_id": info_data.get("device_id"), "buckets": export_data.get("buckets")}

    try:
        logger.warning("Sending export_data to tracer")
        headers = {
            "Authorization": f"Bearer {NEXUS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(NEXUS_API_ENDPOINT, json=payload, headers=headers)
        logger.warning("Export data sent to server")
        logger.warning(f"Response: {response.json()}")
    except Exception as e:
        logger.error(f"Error sending export data to tracer: {e}")


def init_nexus_sync(host, port):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        export_all_data_to_remote_db,
        "cron",
        minute="*/10",  # Runs every 10 minutes
        args=(host, port)
    )
    scheduler.start()


def update_config_var(var_name, new_value):
    """Update a specific variable in config.py without deleting other variables."""

    CONFIG_FILE = "aw_server/nexus_config.py"

    try:
        updated = False
        new_lines = []

        with open(CONFIG_FILE, "r") as file:
            lines = file.readlines()

        for line in lines:
            if re.match(rf"^{var_name}\s*=", line):  # Match variable assignment
                new_lines.append(f'{var_name} = "{new_value}"\n')  # Update value
                updated = True
            else:
                new_lines.append(line)

        # If variable wasn't found, add it at the end
        if not updated:
            new_lines.append(f'{var_name} = "{new_value}"\n')

        with open(CONFIG_FILE, "w") as file:
            file.writelines(new_lines)

        print(f"Updated {var_name} in {CONFIG_FILE} to: {new_value}")

    except Exception as e:
        print(f"Error updating config file: {e}")



def init_settings():
    """Update config file with token from environment variable."""

    # Get the token from an environment variable
    token = os.getenv("NEXUS_API_TOKEN", "sk-nexus-api-key") # Local default token
    api_endpoint = os.getenv("NEXUS_API_ENDPOINT", "https://nexus-core-api-v1-143934872474.europe-north1.run.app/import-buckets-with-events")

    update_config_var("NEXUS_API_TOKEN", token)
    update_config_var("NEXUS_API_ENDPOINT", api_endpoint)
