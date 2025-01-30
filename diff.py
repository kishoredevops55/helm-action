import pandas as pd
from datetime import datetime

# ✅ Step 1: Read application names from text files
def read_app_names(filename):
    """Reads application names from a text file and returns a set of lowercase names."""
    with open(filename, 'r', encoding='utf-8') as file:
        return {line.strip().lower() for line in file if line.strip()}  # Use set for fast lookup

ingestion_app_names = read_app_names('ingestion-app-name-list.txt')
platform_app_names = read_app_names('platform-app-name-list.txt')

# ✅ Step 2: Read Unused Resources from Excel (Excluding "Summary" Sheet)
def read_unused_resources_from_excel(filename):
    """Reads all sheets (except 'Summary') and extracts the first column as a list of resources."""
    xls = pd.ExcelFile(filename)
    sheets = [sheet for sheet in xls.sheet_names if sheet.lower() != "summary"]

    unused_resources = {}
    for sheet in sheets:
        df = xls.parse(sheet, usecols=[0])  # Read only the first column (assuming resource names)
        df.dropna(inplace=True)  # Remove empty rows
        unused_resources[sheet] = df.iloc[:, 0].astype(str).tolist()  # Convert all to string
    return unused_resources

# ✅ Step 3: Categorize Resources
def categorize_resources(unused_resources, ingestion_apps, platform_apps):
    """Categorizes resources into Ingestion, Platform, and DevOps."""
    ingestion_unused_resources = {resource: [] for resource in unused_resources}
    platform_unused_resources = {resource: [] for resource in unused_resources}
    devops_unused_resources = {resource: [] for resource in unused_resources}

    for resource, items in unused_resources.items():
        for item in items:
            item_lower = item.lower()  # Convert to lowercase for case-insensitive matching
            matched = False

            # 🔹 Exact match using set lookup for fast performance
            if any(app in item_lower for app in platform_apps):
                platform_unused_resources[resource].append(item)
                matched = True
            elif any(app in item_lower for app in ingestion_apps):
                ingestion_unused_resources[resource].append(item)
                matched = True
            
            # 🔹 If no match, assign to DevOps
            if not matched:
                devops_unused_resources[resource].append(item)

    return ingestion_unused_resources, platform_unused_resources, devops_unused_resources

# ✅ Step 4: Save Filtered Data to Excel
def save_filtered_results_to_excel(filtered_resources, filename):
    """Saves categorized resources to an Excel file, using separate sheets for each resource type."""
    with pd.ExcelWriter(filename) as writer:
        for resource, items in filtered_resources.items():
            if items:
                df = pd.DataFrame(items, columns=[resource])  # Keep sheet name same as resource
                df.to_excel(writer, sheet_name=resource, index=False)
    print(f"✅ Filtered results saved to '{filename}'")

# ✅ Step 5: Main Execution Flow
if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    input_excel_file = f"unused_k8s_resources_{timestamp}.xlsx"

    # Read data
    unused_resources = read_unused_resources_from_excel(input_excel_file)

    # Categorize resources
    ingestion_results, platform_results, devops_results = categorize_resources(
        unused_resources, ingestion_app_names, platform_app_names
    )

    # Save results
    save_filtered_results_to_excel(ingestion_results, f"ingestion_unused_k8s_resources_{timestamp}.xlsx")
    save_filtered_results_to_excel(platform_results, f"platform_unused_k8s_resources_{timestamp}.xlsx")
    save_filtered_results_to_excel(devops_results, f"devops_unused_k8s_resources_{timestamp}.xlsx")

    print("✅ Processing completed successfully.")
    
