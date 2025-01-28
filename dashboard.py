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
    """Fetch details and usage stats for a single dashboard."""
    # Dashboard details
    dashboard_url = f"{GRAFANA_URL}/api/dashboards/uid/{dashboard['uid']}"
    dashboard_response = requests.get(dashboard_url, headers=HEADERS)
    dashboard_response.raise_for_status()
    dashboard_data = dashboard_response.json()

    # Usage stats (via Annotations API or adjust based on your setup)
    annotations_url = f"{GRAFANA_URL}/api/annotations"
    params = {
        "from": int(LAST_30_DAYS.timestamp() * 1000),  # Convert to milliseconds
        "to": int(NOW.timestamp() * 1000),
        "dashboardId": dashboard["id"],
    }
    annotations_response = requests.get(annotations_url, headers=HEADERS, params=params)
    annotations_response.raise_for_status()
    usage_count = len(annotations_response.json())

    return {
        "Name": dashboard_data["dashboard"]["title"],
        "UID": dashboard['uid'],
        "Folder": dashboard_data["meta"]["folderTitle"],
        "Views (last 30 days)": usage_count,
    }

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
