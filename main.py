#!/usr/bin/env python3

import pandas as pd
import numpy as np
from pathlib import Path
import re
import os


def load_files(folder_path: str) -> dict:
    """
    Load all CSV and Excel files from the given folder_path into DataFrames.
    
    Returns:
        A dictionary where the key is the filename and the value is the DataFrame.
    """

    # Make a clean folder to put the cleaned files
    clean_folder_path = '/workspaces/focused_data_cleanup/cleaned'
    clean_folder = Path(clean_folder_path)

    # Make sure the folder exists (create it if needed)
    clean_folder.mkdir(parents=True, exist_ok=True)



    folder = Path(folder_path)
    data_dict = {}

    # Iterate over all items in the folder
    for file_path in folder.glob('*'):
        # Skip if it's not a file
        if not file_path.is_file():
            continue

        # Check file extension
        ext = file_path.suffix.lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
            data_dict[file_path.name] = df
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
            data_dict[file_path.name] = df

    return data_dict


def bless_df(df, final_df):
    uid_regex = re.compile(r'^\d+$')  # Regex to match strings with only digits

    # Ensure final_df is a DataFrame
    if not isinstance(final_df, pd.DataFrame):
        final_df = pd.DataFrame()

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
            final_df['Phone'] = df[col].apply(lambda x: re.sub(r'\D', '', str(x)))

        elif 'student name' in col_lower:
            clean_names = df[col].str.replace(',', '', regex=False)
            final_df['First Name'] = clean_names.apply(lambda x: x.split(' ')[0] 
                                            if isinstance(x, str) else x)
            final_df['Last Name'] = clean_names.apply(lambda x: ' '.join(x.split(' ')[1:]) 
                                            if isinstance(x, str) and len(x.split(' ')) > 1 else pd.NA)

        # Only if the column doesn't match any known pattern, check if it's numeric UID
        elif df[col].apply(lambda x: bool(uid_regex.match(x))).all():
            final_df['Student UID'] = df[col]

    return final_df






def main():

    #/workspaces/focused_data_cleanup/to_clean
    # Read in your files

    # Create two folder paths relative to the current script (cwd)
    to_clean_folder = os.path.join(os.getcwd(), "to_clean")
    cleaned_folder = os.path.join(os.getcwd(), "cleaned")

    # Make the folders if they don't exist
    os.makedirs(to_clean_folder, exist_ok=True)
    os.makedirs(cleaned_folder, exist_ok=True)

    # Now load CSV files from `to_clean_folder`
    data_dict = load_files(to_clean_folder)


    i = 1
    # Print out the loaded DataFrame names and first few rows as a check
    for filename, df in data_dict.items():
        print(f"=== {filename} ===")
        print("DataFrame before cleaning:")
        print(df.head())

        holy_df = bless_df(df, pd.DataFrame(columns=['Student UID', 'First Name', 'Last Name', 'Grade', 'Teacher', 'Email', 'Phone']))

        # Save the cleaned DataFrame to the cleaned folder
        out_filename = f"Holy_df{i}.csv"
        out_filepath = os.path.join(cleaned_folder, out_filename)
        holy_df.to_csv(out_filepath, index=False)
        i += 1
    
    # Your main code logic here
    print("Program finished. Press Enter to exit.")
    input()





if __name__ == '__main__':
    main()





