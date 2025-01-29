import requests
import pandas as pd
from datetime import datetime, timedelta

# Configuration
GRAFANA_URL = 'https://your-grafana-instance.com'
API_KEY = 'your_api_key'
HEADERS = {'Authorization': f'Bearer {API_KEY}'}

# Calculate the date 30 days ago
thirty_days_ago = datetime.now() - timedelta(days=30)

def get_dashboards():
    """Fetch all dashboards."""
    url = f'{GRAFANA_URL}/api/search?type=dash-db'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_dashboard_details(uid):
    """Fetch dashboard details by UID."""
    url = f'{GRAFANA_URL}/api/dashboards/uid/{uid}'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_dashboard_insights(uid):
    """Fetch dashboard usage insights."""
    url = f'{GRAFANA_URL}/api/dashboards/uid/{uid}/insights'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def main():
    dashboards = get_dashboards()
    data = []

    for dashboard in dashboards:
        uid = dashboard['uid']
        title = dashboard['title']
        folder_title = dashboard.get('folderTitle', 'General')

        # Fetch usage insights
        insights = get_dashboard_insights(uid)
        user_views = insights.get('users', [])

        for user_view in user_views:
            user = user_view.get('name', 'Unknown')
            view_count = user_view.get('count', 0)
            last_viewed = user_view.get('lastViewed', '')

            # Convert last_viewed to datetime
            if last_viewed:
                last_viewed = datetime.strptime(last_viewed, '%Y-%m-%dT%H:%M:%S.%fZ')

            # Filter views in the last 30 days
            if last_viewed and last_viewed >= thirty_days_ago:
                data.append({
                    'Dashboard Name': title,
                    'UID': uid,
                    'Folder': folder_title,
                    'User': user,
                    'View Count': view_count,
                    'Last Viewed': last_viewed
                })

    # Create DataFrame
    df = pd.DataFrame(data)

    # Export to Excel
    df.to_excel('grafana_dashboard_usage.xlsx', index=False)
    print('Data exported to grafana_dashboard_usage.xlsx')

if __name__ == '__main__':
    main()
