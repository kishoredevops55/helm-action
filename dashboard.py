import requests
import pandas as pd
import os
from datetime import datetime, timedelta

# Grafana configuration (Replace or use environment variables)
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://your-grafana-url")  # Replace with your Grafana URL
API_KEY = os.getenv("GRAFANA_API_KEY", "your_api_key")  # Replace with your API key
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Time range for usage stats (last 30 days)
NOW = datetime.now()
LAST_30_DAYS = NOW - timedelta(days=30)

def fetch_dashboards():
    """Fetch the list of all dashboards."""
    url = f"{GRAFANA_URL}/api/search?type=dash-db"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_dashboard_details_and_usage(dashboard):
    """Fetch details and accurate view counts for a single dashboard."""
    # Dashboard metadata
    dashboard_url = f"{GRAFANA_URL}/api/dashboards/uid/{dashboard['uid']}"
    dashboard_response = requests.get(dashboard_url, headers=HEADERS)
    dashboard_response.raise_for_status()
    dashboard_data = dashboard_response.json()

    # Accurate view count via /api/dashboard-stats
    view_count = fetch_view_count(dashboard["id"])

    return {
        "Name": dashboard_data["dashboard"]["title"],
        "UID": dashboard['uid'],
        "Folder": dashboard_data["meta"]["folderTitle"],
        "Views (last 30 days)": view_count,
    }

def fetch_view_count(dashboard_id):
    """Fetch accurate view counts using Grafana's /api/dashboard-stats endpoint."""
    stats_url = f"{GRAFANA_URL}/api/dashboard-stats/{dashboard_id}"
    response = requests.get(stats_url, headers=HEADERS)
    response.raise_for_status()
    stats = response.json()

    # Filter view counts for the last 30 days
    views_last_30_days = 0
    for entry in stats["data"]:
        view_timestamp = datetime.fromtimestamp(entry["timestamp"] / 1000)  # Convert ms to seconds
        if LAST_30_DAYS <= view_timestamp <= NOW:
            views_last_30_days += 1

    return views_last_30_days

def export_to_excel(data):
    """Export the collected data to an Excel file."""
    df = pd.DataFrame(data)
    file_name = f"grafana_dashboard_usage_{NOW.strftime('%Y%m%d')}.xlsx"
    df.to_excel(file_name, index=False, engine="openpyxl")
    print(f"Data exported successfully to: {file_name}")

def main():
    """Main function to fetch and export dashboard data."""
    try:
        print("Fetching dashboards...")
        dashboards = fetch_dashboards()
        
        print("Processing dashboards...")
        dashboard_data = [fetch_dashboard_details_and_usage(dashboard) for dashboard in dashboards]

        print("Exporting data to Excel...")
        export_to_excel(dashboard_data)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
    
