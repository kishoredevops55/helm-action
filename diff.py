import pandas as pd
from datetime import datetime

# Read application names from text files
def read_app_names(filename):
    with open(filename, 'r') as file:
        return [line.strip().lower() for line in file.readlines()]

ingestion_app_names = read_app_names('ingestion-app-name-list.txt')
platform_app_names = read_app_names('platform-app-name-list.txt')

# Read unused resources from Excel file (excluding "Summary" sheet)
def read_unused_resources_from_excel(filename):
    xls = pd.ExcelFile(filename)
    sheets = [sheet for sheet in xls.sheet_names if sheet.lower() != "summary"]
    
    unused_resources = {}
    for sheet in sheets:
        df = xls.parse(sheet)
        resource_name = sheet  # Using sheet name as resource type
        unused_resources[resource_name] = df.iloc[:, 0].dropna().tolist()  # Assume first column has resource names
    return unused_resources

# Generate timestamp and output filenames
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
output_filename = f"unused_k8s_resources_{timestamp}.xlsx"

unused_resources = read_unused_resources_from_excel(output_filename)

# Initialize dictionaries for filtered resources
ingestion_unused_resources = {resource: [] for resource in unused_resources}
platform_unused_resources = {resource: [] for resource in unused_resources}
devops_unused_resources = {resource: [] for resource in unused_resources}

# Categorize resources based on application names
for resource, items in unused_resources.items():
    for item in items:
        matched = False
        
        # Check if the item matches any platform application
        if any(app in item.lower() for app in platform_app_names):
            platform_unused_resources[resource].append(item)
            matched = True
        
        # Check if the item matches any ingestion application
        if not matched and any(app in item.lower() for app in ingestion_app_names):
            ingestion_unused_resources[resource].append(item)
            matched = True

        # If no match is found, assign to DevOps
        if not matched:
            devops_unused_resources[resource].append(item)

# Save filtered results to separate Excel files
def save_filtered_results_to_excel(filtered_resources, filename):
    with pd.ExcelWriter(filename) as writer:
        for resource, items in filtered_resources.items():
            if items:
                df = pd.DataFrame(items, columns=["Unused " + resource])
                df.to_excel(writer, sheet_name=resource, index=False)
    print(f"Filtered results saved to '{filename}'")

save_filtered_results_to_excel(ingestion_unused_resources, f"ingestion_unused_k8s_resources_{timestamp}.xlsx")
save_filtered_results_to_excel(platform_unused_resources, f"platform_unused_k8s_resources_{timestamp}.xlsx")
save_filtered_results_to_excel(devops_unused_resources, f"devops_unused_k8s_resources_{timestamp}.xlsx")

print("Processing completed.")
