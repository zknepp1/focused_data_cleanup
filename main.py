#!/usr/bin/env python3

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import re
import os
import openpyxl


def setup_logger():
    """
    Set up a logger that outputs to both the console and a file called 'my_program.log'.
    """
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)  # Overall log level

    # Create a file handler which logs even debug messages
    fh = logging.FileHandler("my_program.log", mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create a formatter and set it for both handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger





def load_files(folder_path: str, logger: logging.Logger) -> dict:
    """
    Load all CSV and Excel files from the given folder_path into DataFrames.
    
    Returns:
        A dictionary where the key is the filename and the value is the DataFrame.
    """

    logger.info(f"Loading files from folder: {folder_path}")


    folder = Path(folder_path)
    data_dict = {}

    # List of encodings to try for CSV files
    encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1', 'utf-16']

    # Iterate over all items in the folder
    for file_path in folder.glob('*'):
        # Skip if it's not a file
        if not file_path.is_file():
            logger.debug(f"Skipping non-file path: {file_path}")
            continue

        # Check file extension
        ext = file_path.suffix.lower()

        try:
            if ext == '.csv':
                for encoding in encodings_to_try:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        data_dict[file_path.name] = df
                        logger.info(f"Successfully loaded CSV file: {file_path.name} with encoding {encoding}")
                        break
                    except UnicodeDecodeError:
                        logger.warning(f"Failed to decode {file_path.name} with encoding {encoding}")
                else:
                    logger.error(f"Unable to load CSV file {file_path.name} with any tested encoding.")


            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
                data_dict[file_path.name] = df
                logger.info(f"Successfully loaded Excel file: {file_path.name}")

            else:
                logger.debug(f"Skipping unsupported file format: {file_path.name}")

        except Exception as e:
            logger.error(f"Error loading file {file_path.name}: {e}", exc_info=True)


    return data_dict


def bless_df(df, final_df, logger: logging.Logger):
    """
    Clean and map DataFrame columns to a final, standardized DataFrame format.
    """
    logger.debug("Starting DataFrame cleanup process.")

    # Regex for detecting numeric student IDs (no fixed length)
    uid_regex = re.compile(r'^\d+$')

    # Columns that should NEVER be mistaken for Student ID
    excluded_columns = {"site", "location", "building"}  

    # Ensure final_df is a DataFrame
    if not isinstance(final_df, pd.DataFrame):
        final_df = pd.DataFrame()

    try:
        df = df.astype(str).dropna(how='all').reset_index(drop=True)
        final_df = final_df.reindex(df.index, fill_value=pd.NA)

        # Identify the best column to use as 'Student UID'
        possible_uid_cols = {}

        for col in df.columns:
            col_lower = col.lower()

            # Exclude known non-ID columns
            if col_lower in excluded_columns:
                logger.debug(f"Skipping known non-ID column: {col}")
                continue

            # Check for numeric values
            numeric_values = df[col].apply(lambda x: x.isdigit())
            valid_ids = df[col][numeric_values].apply(lambda x: bool(uid_regex.match(x)))

            # Ensure the column has enough unique values (avoid static values like "705" for all rows)
            unique_values = df[col][valid_ids].nunique()
            if valid_ids.sum() > 0 and unique_values > 5:  # Ensure it's not just 1-2 repeated values
                possible_uid_cols[col] = valid_ids.sum()

        if possible_uid_cols:
            # Pick the column with the most valid numeric entries
            best_uid_col = max(possible_uid_cols, key=possible_uid_cols.get)
            final_df['Student UID'] = df[best_uid_col]
            logger.info(f"Identified Student ID column: {best_uid_col}")
        else:
            logger.warning("No valid Student ID column found.")

        # Process other relevant fields
        for col in df.columns:
            col_lower = col.lower()

            if 'grade' in col_lower:
                final_df['Grade'] = df[col]
            elif 'last' in col_lower:
                final_df['Last Name'] = df[col].apply(lambda x: x.capitalize() if isinstance(x, str) else x)
            elif 'first' in col_lower:
                final_df['First Name'] = df[col].apply(lambda x: x.capitalize() if isinstance(x, str) else x)
            elif 'email' in col_lower:
                final_df['Email'] = df[col]
            elif 'home' in col_lower or 'teacher' in col_lower:
                final_df['Teacher'] = df[col].apply(lambda x: x.split(',')[0].strip() if pd.notna(x) else x)
            elif 'phone' in col_lower:
                final_df['Phone'] = df[col].apply(lambda x: re.sub(r'\D', '', str(x)))  # Remove non-numeric characters
            elif col_lower in excluded_columns:
                final_df[col] = df[col]  # Preserve excluded columns like "Site"

        logger.debug("DataFrame cleanup and mapping completed successfully.")

    except Exception as e:
        logger.error(f"Error in bless_df: {e}", exc_info=True)

    final_df = final_df.fillna('')

    return final_df



def main():
    # Initialize logger
    logger = setup_logger()
    logger.info("Starting the program...")
    try:
        # Create folder paths relative to the current script (cwd)
        to_clean_folder = os.path.join(os.getcwd(), "to_clean")
        cleaned_folder = os.path.join(os.getcwd(), "cleaned")

        # Make the folders if they don't exist
        os.makedirs(to_clean_folder, exist_ok=True)
        os.makedirs(cleaned_folder, exist_ok=True)
        logger.debug(f"Ensured 'to_clean' and 'cleaned' folders exist in {os.getcwd()}")

        # Load files
        data_dict = load_files(to_clean_folder, logger)

        # Process and save each DataFrame
        i = 1
        for filename, df in data_dict.items():
            logger.info(f"Processing file: {filename}")
            holy_df = bless_df(
                df, 
                pd.DataFrame(columns=['Student UID', 'First Name', 'Last Name', 'Grade', 'Teacher', 'Email', 'Phone']),
                logger
            )

            # Generate the cleaned filename
            cleaned_filename = f"{os.path.splitext(filename)[0]}_cleaned.csv"
            out_filepath = os.path.join(cleaned_folder, cleaned_filename)

            try:
                holy_df.to_csv(out_filepath, index=False)
                logger.info(f"Cleaned data saved to: {out_filepath}")
            except Exception as e:
                logger.error(f"Failed to save cleaned DataFrame for {filename}: {e}", exc_info=True)

            i += 1

    except Exception as e:
        logger.exception("An unhandled exception occurred in main:")

    logger.info("Program finished. Press Enter to exit.")
    input()





if __name__ == '__main__':
    main()





