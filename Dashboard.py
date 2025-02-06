import requests
import os
import pandas as pd
from datetime import datetime
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "https://example.com/grafana")
API_KEY = os.getenv("GRAFANA_API_KEY")
if not API_KEY or not API_KEY.strip():
    raise ValueError("GRAFANA_API_KEY is not set or empty")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

SEARCH_API_URL = f"{GRAFANA_URL}/api/search-v2"
USAGE_STATS_API_URL = f"{GRAFANA_URL}/api/usagestats/dashboards"

# Payload for fetching dashboards
payload = {
    "query": "+",
    "tags": [],
    "sort": "-views_last_30_days",
    "starred": False,
    "deleted": False,
    "kind": ["dashboard"],
    "limit": 5000
}

def fetch_dashboards() -> dict:
    """Fetch dashboards sorted by views in the last 30 days."""
    try:
        response = requests.post(SEARCH_API_URL, json=payload, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error in fetch_dashboards: {e}")
        return {}

def fetch_dashboard_details(uid: str) -> dict:
    """For a given dashboard UID, retrieve detailed info including creator, last editor, and last viewer."""
    details_url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    try:
        response = requests.get(details_url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        details = response.json()
        
        dashboard = details.get("dashboard", {})
        meta = details.get("meta", {})

        # Extract dashboard details
        dashboard_title = dashboard.get("title", "Unknown Dashboard")
        folder_title = meta.get("folderTitle", "General")
        created_by = meta.get("createdBy", "Unknown")
        created_date = meta.get("created", "")
        edited_by = meta.get("updatedBy", "Unknown")
        edited_date = meta.get("updated", "")
        
        # Fetch last viewed user via Usage Stats API
        last_viewed_user, last_viewed_date = fetch_last_viewed_user(uid)

        # Convert timestamps
        created_date = format_timestamp(created_date)
        edited_date = format_timestamp(edited_date)
        last_viewed_date = format_timestamp(last_viewed_date)

        if folder_title == "General":
            folder_title = "Dashboards"

        return {
            "Dashboard Name": dashboard_title,
            "UID": uid,
            "Folder Path": folder_title,
            "Created By": created_by,
            "Creation Date": created_date,
            "Last Edited By": edited_by,
            "Last Edited Date": edited_date,
            "Last Viewed By": last_viewed_user,
            "Last Viewed Date": last_viewed_date
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error for UID '{uid}': {e}")
        return {}

def fetch_last_viewed_user(uid: str) -> tuple:
    """Fetch the last viewed user and timestamp from the Usage Stats API."""
    try:
        response = requests.get(f"{USAGE_STATS_API_URL}/{uid}", headers=HEADERS, timeout=5)
        response.raise_for_status()
        stats = response.json()

        # Get last viewed user and date
        last_viewed_user = stats.get("lastViewedUser", "Unknown")
        last_viewed_date = stats.get("lastViewed", "")
        
        return last_viewed_user, last_viewed_date
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error for UID '{uid}' in Usage Stats API: {e}")
        return "Unknown", "Unknown"

def format_timestamp(timestamp: str) -> str:
    """Convert timestamp to human-readable format."""
    try:
        if timestamp:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    return "Unknown"

def extract_dashboard_data(dashboards: dict) -> list:
    """Extracts dashboard data including ownership and timestamps."""
    data = []
    if not isinstance(dashboards, dict) or "frames" not in dashboards:
        logging.error("Unexpected response structure from search-v2.")
        return data

    try:
        for item in dashboards["frames"]:
            values = item.get("data", {}).get("values", [])
            if len(values) < 9:
                logging.warning("Unexpected data structure in item; skipping.")
                continue

            uids = values[1]
            views = values[8]

            if len(uids) != len(views):
                logging.warning("Mismatch in UIDs and Views lengths.")
                continue

            for uid, view in zip(uids, views):
                details = fetch_dashboard_details(uid)
                if details:
                    details["Views (Last 30 Days)"] = view
                    data.append(details)
                time.sleep(0.1)  # Throttle API calls
    except Exception as e:
        logging.error(f"Error extracting dashboard data: {e}")

    return data

def sort_dashboard_data(data: list) -> pd.DataFrame:
    """Sort the dashboard data by views."""
    df = pd.DataFrame(data)
    return df.sort_values(by="Views (Last 30 Days)", ascending=True)

def export_to_excel(df: pd.DataFrame, filename: str) -> None:
    """Exports the sorted DataFrame to an Excel file."""
    if df.empty:
        logging.warning("No data to export.")
        return

    try:
        df.to_excel(filename, index=False, engine="openpyxl")
        logging.info(f"Data exported successfully to: {filename}")
    except Exception as e:
        logging.error(f"Error exporting data to Excel: {e}")

def main() -> None:
    """Main function to fetch, process, and export dashboard data."""
    try:
        dashboards = fetch_dashboards()
        dashboard_data = extract_dashboard_data(dashboards)
        sorted_df = sort_dashboard_data(dashboard_data)
        export_to_excel(sorted_df, "grafana_dashboard_usage.xlsx")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
    
