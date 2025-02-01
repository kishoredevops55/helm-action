import pandas as pd
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Define input and output file paths
INPUT_FILE = "A.xlsx"
PLATFORM_KEYWORDS_FILE = "platform_apps.txt"
INGESTION_KEYWORDS_FILE = "ingestion_apps.txt"

# Define output files
OUTPUT_PLATFORM = "Platform.xlsx"
OUTPUT_INGESTION = "Ingestion.xlsx"
OUTPUT_DEVOPS = "DevOps.xlsx"

def load_keywords(filename):
    """Load keywords from a text file into a list."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            keywords = [line.strip().lower() for line in file if line.strip()]
        return keywords
    except FileNotFoundError:
        logging.warning(f"File '{filename}' not found. Proceeding without it.")
        return []

def main():
    # Load keywords
    platform_keywords = load_keywords(PLATFORM_KEYWORDS_FILE)
    ingestion_keywords = load_keywords(INGESTION_KEYWORDS_FILE)

    if not platform_keywords and not ingestion_keywords:
        logging.warning("No keywords loaded. All data will go to DevOps.xlsx")

    # Compile regex patterns
    platform_regex = re.compile("|".join(map(re.escape, platform_keywords)), re.IGNORECASE) if platform_keywords else None
    ingestion_regex = re.compile("|".join(map(re.escape, ingestion_keywords)), re.IGNORECASE) if ingestion_keywords else None

    # Initialize DataFrames
    df_platform = pd.DataFrame()
    df_ingestion = pd.DataFrame()
    df_devops = pd.DataFrame()

    try:
        with pd.ExcelFile(INPUT_FILE) as xls:
            for sheet_name in xls.sheet_names:
                if sheet_name.lower() == "summary":
                    logging.info(f"Skipping 'summary' sheet.")
                    continue  # Skip the summary sheet

                logging.info(f"Processing sheet: {sheet_name}")
                try:
                    # Read the sheet and detect column names dynamically
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    
                    if df.empty:
                        logging.warning(f"Sheet '{sheet_name}' is empty. Skipping.")
                        continue

                    # Assume the first column contains app names
                    first_col_name = df.columns[0]  # Dynamically get the first column name
                    
                    # Clean data
                    df_clean = df[[first_col_name]].dropna()
                    df_clean[first_col_name] = df_clean[first_col_name].astype(str).str.strip().str.lower()
                    
                    if df_clean.empty:
                        logging.warning(f"No valid data in column '{first_col_name}' for sheet '{sheet_name}'. Skipping.")
                        continue

                    # Apply regex-based filtering
                    mask_platform = df_clean[first_col_name].str.contains(platform_regex, regex=True, na=False) if platform_regex else pd.Series(False, index=df_clean.index)
                    mask_ingestion = df_clean[first_col_name].str.contains(ingestion_regex, regex=True, na=False) if ingestion_regex else pd.Series(False, index=df_clean.index)

                    # Append matches to respective DataFrames
                    df_platform = pd.concat([df_platform, df_clean[mask_platform]], ignore_index=True)
                    df_ingestion = pd.concat([df_ingestion, df_clean[mask_ingestion]], ignore_index=True)
                    df_devops = pd.concat([df_devops, df_clean[~(mask_platform | mask_ingestion)]], ignore_index=True)

                except Exception as e:
                    logging.error(f"Error processing sheet '{sheet_name}': {e}")
                    continue

        # Ensure output files are created even if empty
        df_platform.to_excel(OUTPUT_PLATFORM, index=False)
        df_ingestion.to_excel(OUTPUT_INGESTION, index=False)
        df_devops.to_excel(OUTPUT_DEVOPS, index=False)

        logging.info(f"Processing complete! Output saved to {OUTPUT_PLATFORM}, {OUTPUT_INGESTION}, {OUTPUT_DEVOPS}")

    except FileNotFoundError:
        logging.error(f"Input file '{INPUT_FILE}' not found.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
    
