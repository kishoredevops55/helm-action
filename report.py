import requests
import pandas as pd
import os
from datetime import datetime

# Grafana configuration (Replace or use environment variables)
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://your-grafana-url")  # Replace with your Grafana URL
API_KEY = os.getenv("GRAFANA_API_KEY", "your_api_key")  # Replace with your API key
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Current date for file naming
NOW = datetime.now()

def fetch_usage_report():
    """Fetch the dashboard usage report from Grafana Enterprise."""
    url = f"{GRAFANA_URL}/api/usage-report/dashboards"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def process_usage_report(report):
    """Process the usage report to extract required fields."""
    dashboard_data = []
    for entry in report["data"]:
        dashboard_data.append({
            "Name": entry["dashboardTitle"],
            "UID": entry["dashboardUid"],
            "Folder": entry["folderTitle"],
            "Views (last 30 days)": entry["viewsLast30Days"],
            "Least Views Rank": entry.get("leastViewedRank", "N/A"),  # Only available in Enterprise
            "Most Views Rank": entry.get("mostViewedRank", "N/A"),   # Only available in Enterprise
        })
    return dashboard_data

def export_to_excel(data):
    """Export the processed data to an Excel file."""
    df = pd.DataFrame(data)
    file_name = f"grafana_dashboard_usage_{NOW.strftime('%Y%m%d')}.xlsx"
    df.to_excel(file_name, index=False, engine="openpyxl")
    print(f"Data exported successfully to: {file_name}")

def main():
    """Main function to fetch, process, and export the usage report."""
    try:
        print("Fetching dashboard usage report...")
        usage_report = fetch_usage_report()
        
        print("Processing usage report...")
        dashboard_data = process_usage_report(usage_report)

        print("Exporting data to Excel...")
        export_to_excel(dashboard_data)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
