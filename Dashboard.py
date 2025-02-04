import requests
import pandas as pd
from datetime import datetime

# Set your Grafana URL and API Key
GRAFANA_URL = "https://your-grafana-instance.com"  # Replace with your Grafana URL
API_KEY = "your_api_key_here"  # Replace with your actual API key

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def fetch_all_dashboards():
    """Fetch all dashboards, ensuring none are missing by handling pagination."""
    url = f"{GRAFANA_URL}/api/search"
    dashboards = []
    page = 1
    limit = 50  # Process dashboards in batches

    while True:
        params = {
            "query": "",
            "type": "dash-db",
            "sort": "views_last_30_days",
            "order": "desc",
            "limit": limit,
            "page": page  # Paginate through results
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            batch = response.json()

            if not batch:
                break  # Stop if no more dashboards are found

            dashboards.extend(batch)
            page += 1  # Move to the next page

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break

    return dashboards

def fetch_dashboard_details(uid):
    """Fetch the dashboard name and full folder path using the dashboard UID."""
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        dashboard_info = response.json()
        
        dashboard_name = dashboard_info.get("dashboard", {}).get("title", "Unknown Dashboard")
        folder_title = dashboard_info.get("meta", {}).get("folderTitle", "General")  # Correct folder name

        return dashboard_name, folder_title
    except requests.exceptions.RequestException:
        return "Unknown Dashboard", "Unknown Folder"

def main():
    dashboards = fetch_all_dashboards()
    if not dashboards:
        print("Unexpected response structure or missing dashboards")
        return

    data = []
    
    for item in dashboards:
        uid = item.get("uid")
        view_count = item.get("viewCount", 0)  # Extract views directly

        dashboard_name, folder_path = fetch_dashboard_details(uid)

        data.append({
            "Dashboard Name": dashboard_name,  
            "UID": uid,
            "Folder Path": folder_path,  # Now correctly fetching folder path
            "Views (Last 30 Days)": view_count
        })

    # Export to Excel
    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"grafana_dashboard_usage_{current_time}.xlsx"
    df.to_excel(excel_filename, index=False, engine="openpyxl")

    print(f"Data exported successfully to: {excel_filename}")

if __name__ == "__main__":
    main()
    
