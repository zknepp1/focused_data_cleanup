#!/usr/bin/env python3

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import re
import os


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
                df = pd.read_csv(file_path)
                data_dict[file_path.name] = df
                logger.info(f"Successfully loaded CSV file: {file_path.name}")

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

    uid_regex = re.compile(r'^\d+$')  # Regex to match strings with only digits

    # Ensure final_df is a DataFrame
    if not isinstance(final_df, pd.DataFrame):
        final_df = pd.DataFrame()


    try:
        # Clean the input df
        df = df.astype(str)
        df = df.dropna(how='all').reset_index(drop=True)

        # Reindex final_df to match df after cleaning
        final_df = final_df.reindex(df.index, fill_value=pd.NA)

        for col in df.columns:
            col_lower = col.lower()

            # Check for known columns first, before numeric pattern
            if 'grade' in col_lower:
                final_df['Grade'] = df[col]

            elif 'last' in col_lower:
                final_df['Last Name'] = df[col]

            elif 'first' in col_lower:
                final_df['First Name'] = df[col]

            elif 'email' in col_lower:
                final_df['Email'] = df[col]

            elif 'teacher' in col_lower or 'homeroom' in col_lower:
                final_df['Teacher'] = df[col].apply(lambda x: x.split(',')[0].strip() if pd.notna(x) else x)

            elif 'phone' in col_lower:
                # Replace non-digit characters
                final_df['Phone'] = df[col].apply(lambda x: re.sub(r'\D', '', str(x)))

            elif 'student name' in col_lower:
                # Example of splitting on spaces
                clean_names = df[col].str.replace(',', '', regex=False)
                final_df['First Name'] = clean_names.apply(
                    lambda x: x.split(' ')[0] if isinstance(x, str) else x
                )
                final_df['Last Name'] = clean_names.apply(
                    lambda x: ' '.join(x.split(' ')[1:]) 
                    if isinstance(x, str) and len(x.split(' ')) > 1 else pd.NA
                )

            # If the column doesn't match a known pattern, check for numeric UID
            elif df[col].apply(lambda x: bool(uid_regex.match(x))).all():
                final_df['Student UID'] = df[col]

        logger.debug("DataFrame cleanup and mapping completed successfully.")

    except Exception as e:
        logger.error(f"Error in bless_df: {e}", exc_info=True)


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

            out_filename = f"Holy_df{i}.csv"
            out_filepath = os.path.join(cleaned_folder, out_filename)

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





