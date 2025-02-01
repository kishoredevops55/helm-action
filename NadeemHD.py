import pandas as pd
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Define input and output file paths
INPUT_FILE = "A.xlsx"
COLUMN_NAME = "A"  # Change this if your column has a different name
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
    platform_regex = re.compile(r"\b(" + "|".join(map(re.escape, platform_keywords)) + r")\b", re.IGNORECASE) if platform_keywords else None
    ingestion_regex = re.compile(r"\b(" + "|".join(map(re.escape, ingestion_keywords)) + r")\b", re.IGNORECASE) if ingestion_keywords else None

    # Initialize DataFrames
    df_platform = pd.DataFrame(columns=[COLUMN_NAME])
    df_ingestion = pd.DataFrame(columns=[COLUMN_NAME])
    df_devops = pd.DataFrame(columns=[COLUMN_NAME])

    try:
        with pd.ExcelFile(INPUT_FILE) as xls:
            for sheet_name in xls.sheet_names:
                logging.info(f"Processing sheet: {sheet_name}")
                try:
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                    # Validate column exists
                    if COLUMN_NAME not in df.columns:
                        logging.warning(f"Column '{COLUMN_NAME}' not found in sheet '{sheet_name}'. Skipping.")
                        continue

                    # Clean and normalize data
                    df_clean = df[[COLUMN_NAME]].dropna()
                    df_clean[COLUMN_NAME] = df_clean[COLUMN_NAME].astype(str).str.strip().str.lower()

                    if df_clean.empty:
                        logging.warning(f"No data in column '{COLUMN_NAME}' for sheet '{sheet_name}'. Skipping.")
                        continue

                    # Vectorized regex matching
                    mask_platform = df_clean[COLUMN_NAME].str.contains(platform_regex, regex=True) if platform_regex else False
                    mask_ingestion = df_clean[COLUMN_NAME].str.contains(ingestion_regex, regex=True) if ingestion_regex else False

                    # Append matches
                    df_platform = pd.concat([df_platform, df_clean.loc[mask_platform]], ignore_index=True)
                    df_ingestion = pd.concat([df_ingestion, df_clean.loc[mask_ingestion]], ignore_index=True)
                    df_devops = pd.concat([df_devops, df_clean.loc[~(mask_platform | mask_ingestion)]], ignore_index=True)

                except Exception as e:
                    logging.error(f"Error processing sheet '{sheet_name}': {e}")
                    continue

        # Write to separate Excel files
        df_platform.to_excel(OUTPUT_PLATFORM, index=False)
        df_ingestion.to_excel(OUTPUT_INGESTION, index=False)
        df_devops.to_excel(OUTPUT_DEVOPS, index=False)

        logging.info(f"Processing complete! Output files: {OUTPUT_PLATFORM}, {OUTPUT_INGESTION}, {OUTPUT_DEVOPS}")

    except FileNotFoundError:
        logging.error(f"Input file '{INPUT_FILE}' not found.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
    
