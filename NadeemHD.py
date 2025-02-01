import pandas as pd
import re
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_keywords(filename):
    """Load keywords from a text file into a list."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            keywords = [line.strip().lower() for line in file if line.strip()]
        return keywords
    except FileNotFoundError:
        logging.warning(f"File '{filename}' not found. Proceeding without it.")
        return []

def main(input_file, output_file, platform_keywords_file, ingestion_keywords_file, column_name):
    # Load keywords
    platform_keywords = load_keywords(platform_keywords_file)
    ingestion_keywords = load_keywords(ingestion_keywords_file)

    if not platform_keywords and not ingestion_keywords:
        logging.warning("No keywords loaded. All data will be categorized under 'DevOps'.")

    # Compile regex patterns
    platform_regex = re.compile(r"\b(" + "|".join(map(re.escape, platform_keywords)) + r")\b", re.IGNORECASE) if platform_keywords else None
    ingestion_regex = re.compile(r"\b(" + "|".join(map(re.escape, ingestion_keywords)) + r")\b", re.IGNORECASE) if ingestion_keywords else None

    try:
        with pd.ExcelFile(input_file) as xls:
            with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                # Initialize empty DataFrames with the target column name
                df_platform = pd.DataFrame(columns=[column_name])
                df_ingestion = pd.DataFrame(columns=[column_name])
                df_devops = pd.DataFrame(columns=[column_name])

                for sheet_name in xls.sheet_names:
                    logging.info(f"Processing sheet: {sheet_name}")
                    try:
                        # Read the sheet and validate the column exists
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        if column_name not in df.columns:
                            logging.warning(f"Column '{column_name}' not found in sheet '{sheet_name}'. Skipping.")
                            continue

                        # Clean the data (strip whitespace, convert to lowercase)
                        df_clean = df[[column_name]].dropna()
                        df_clean[column_name] = df_clean[column_name].astype(str).str.strip().str.lower()

                        # Skip empty sheets after cleanup
                        if df_clean.empty:
                            logging.warning(f"No data in column '{column_name}' for sheet '{sheet_name}'. Skipping.")
                            continue

                        # Vectorized regex matching
                        mask_platform = df_clean[column_name].str.contains(platform_regex, regex=True) if platform_regex else False
                        mask_ingestion = df_clean[column_name].str.contains(ingestion_regex, regex=True) if ingestion_regex else False

                        # Append matches to respective DataFrames
                        df_platform = pd.concat([df_platform, df.loc[mask_platform, [column_name]]], ignore_index=True)
                        df_ingestion = pd.concat([df_ingestion, df.loc[mask_ingestion, [column_name]]], ignore_index=True)
                        df_devops = pd.concat([df_devops, df.loc[~(mask_platform | mask_ingestion), [column_name]]], ignore_index=True)

                    except Exception as e:
                        logging.error(f"Error processing sheet '{sheet_name}': {e}")
                        continue

                # Write results to Excel (even if empty)
                df_platform.to_excel(writer, sheet_name="Platform", index=False)
                df_ingestion.to_excel(writer, sheet_name="Ingestion", index=False)
                df_devops.to_excel(writer, sheet_name="DevOps", index=False)

        logging.info(f"Processing complete! Output saved to {output_file}")

    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize app names dynamically across sheets and columns.")
    parser.add_argument("input_file", help="Path to the input Excel file (e.g., A.xlsx)")
    parser.add_argument("output_file", help="Path to the output Excel file (e.g., output.xlsx)")
    parser.add_argument("--platform_keywords", default="platform_apps.txt", help="Path to the platform keywords file")
    parser.add_argument("--ingestion_keywords", default="ingestion_apps.txt", help="Path to the ingestion keywords file")
    parser.add_argument("--column", default="A", help="Name of the column to process (e.g., 'AppName', 'Services')")

    args = parser.parse_args()

    main(args.input_file, args.output_file, args.platform_keywords, args.ingestion_keywords, args.column)
