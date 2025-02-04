import logging
import requests
import pandas as pd
from datetime import datetime

# Configuration
GRAFANA_URL = "https://your-grafana-instance.com"  # Replace with your Grafana URL
API_TOKEN = "your_api_token"  # Replace with your Grafana API token
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_dashboards():
    url = f"{GRAFANA_URL}/api/search"
    body = {
        "query": "",
        "tags": [],
        "sort": "-views_last_30_days",
        "starred": False,
        "deleted": False,
        "kind": ["dashboard"],  # Removed "folder" as we only care about dashboards
        "limit": 5000  # Increased limit to a more reasonable number. Grafana API might have limits.
    }
    
    try:
        response = requests.post(url, json=body, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        if response.status_code == 401:  # Example of more specific error handling
            logging.error("Check your API token. It might be incorrect or have insufficient permissions.")
        return None

def main():
    try:
        dashboards = fetch_dashboards()
        if not dashboards:
            logging.warning("No dashboards received. Check your Grafana URL and API token.")
            return

        data = []
        for item in dashboards:
            try:
                dashboard_data = {
                    "name": item.get('title'),
                    "folder": item.get('folderTitle', 'General'),
                    "views_last_30_days": item.get('views_last_30_days', 0),
                    "url": f"{GRAFANA_URL}{item.get('url')}",
                    "uid": item.get('uid'),
                    "created": item.get('created'),
                    "updated": item.get('updated')
                }
                data.append(dashboard_data)
            except Exception as e:
                logging.error(f"Error processing dashboard {item.get('title')}: {e}")

        # Create DataFrame
        df = pd.DataFrame(data)

        # Add timestamp to filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"dashboard_usage_{current_time}.xlsx"
        
        # Sort and export to Excel
        df.sort_values(by='views_last_30_days', ascending=False, inplace=True)
        df.to_excel(excel_filename, index=False)
        logging.info(f"Data exported successfully to {excel_filename}")

        # Optional: Save as CSV as well
        df.to_csv(f"dashboard_usage_{current_time}.csv", index=False)
        logging.info(f"Data also exported as CSV.")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
    
