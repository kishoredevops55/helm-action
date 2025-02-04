import requests
import pandas as pd
from datetime import datetime

# Configuration
GRAFANA_URL = "https://your-grafana-instance.com"
API_TOKEN = "your_api_token"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_dashboards():
    url = f"{GRAFANA_URL}/api/search"
    body = {
        "query": "",
        "tags": [],
        "sort": "-views_last_30_days",
        "starred": False,
        "deleted": False,
        "kind": ["dashboard", "folder"],
        "limit": 1777
    }
    
    try:
        response = requests.post(url, json=body, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def main():
    try:
        dashboards = fetch_dashboards()
        if not dashboards:
            print("No dashboards received")
            return

        # Process dashboard data
        data = []
        for item in dashboards:
            if item.get('type') != 'dash-db':
                continue  # Skip folders and other non-dashboard items
                
            try:
                dashboard_data = {
                    "name": item.get('title'),
                    "folder": item.get('folderTitle', 'General'),
                    "views_last_30_days": item.get('views_last_30_days', 0),
                    "url": f"{GRAFANA_URL}{item.get('url')}",  # Construct full URL
                    "uid": item.get('uid'),
                    "created": item.get('created'),
                    "updated": item.get('updated')
                }
                data.append(dashboard_data)
            except Exception as e:
                print(f"Error processing dashboard {item.get('title')}: {e}")

        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add timestamp to filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"dashboard_usage_{current_time}.xlsx"
        
        # Save to Excel
        df.sort_values(by='views_last_30_days', ascending=False, inplace=True)
        df.to_excel(excel_filename, index=False)
        print(f"Data exported successfully to {excel_filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
