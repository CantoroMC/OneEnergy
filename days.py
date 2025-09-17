import requests
import os
import zipfile
import io
import pandas as pd
from datetime import date, datetime, timedelta
import xml.etree.ElementTree as ET
import glob
import re

# Default output paths for GME data
DEFAULT_OUTPUT_PATH = r"sources\GME\EE"  # Electricity

def download_gme_xml_current_month(output_path=DEFAULT_OUTPUT_PATH):
    """
    Download XML price data from GME for the current month (up to tomorrow)
    Let the server decide if data is available - we try up to tomorrow

    Returns:
        list: List of extracted XML file paths
    """
    from datetime import datetime
    import re

    # Calculate current month dates (up to tomorrow, let server tell us if not ready)
    today = datetime.now()
    data_inizio = today.replace(day=1).strftime("%Y%m%d")
    # Try up to tomorrow - server will return what's available
    data_fine = (today + timedelta(days=1)).strftime("%Y%m%d")
    date_param = (
        today.replace(day=1).replace(month=today.month-1)
            if today.month > 1 else today.replace(day=1).replace(month=12, year=today.year-1)
    ).strftime("%Y%m%d")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Referer': 'https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download?valore=Prezzi',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'ModuleId': '12103',
        'TabId': '1749',
        'UserId': '-1'
    })

    try:
        print("Getting CSRF token...")
        page_response = session.get("https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download", timeout=10)
        if page_response.status_code == 200:
            csrf_match = re.search(r'<input[^>]*name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)["\']', page_response.text)
            csrf_token = csrf_match.group(1) if csrf_match else None
            if csrf_token:
                print(f"Found CSRF token: {csrf_token[:20]}...")
        else:
            print(f"Page visit failed: {page_response.status_code}")
            csrf_token = None
    except Exception as e:
        print(f"Warning: Could not get CSRF token: {e}")
        csrf_token = None

    params = {
        'DataInizio': data_inizio,
        'DataFine': data_fine,
        'Date': date_param,
        'Mercato': 'MGP',
        'Settore': 'Prezzi',
        'FiltroDate': 'InizioFine'
    }
    if csrf_token:
        params['__RequestVerificationToken'] = csrf_token

    try:
        print(f"Downloading XML data for current month ({data_inizio} to {data_fine})...")

        url = "https://gme.mercatoelettrico.org/DesktopModules/GmeDownload/API/ExcelDownload/downloadzipfile"
        response = session.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"HTTP Error {response.status_code}")
            return None

        os.makedirs(output_path, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_ref:
            xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]

            extracted_files = []
            for xml_file in xml_files:
                xml_content = zip_ref.read(xml_file)
                xml_filepath = os.path.join(output_path, xml_file)

                with open(xml_filepath, 'wb') as f:
                    f.write(xml_content)

                extracted_files.append(xml_filepath)
                print(f"Extracted: {xml_file} ({len(xml_content)} bytes)")

            return extracted_files

    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def get_existing_dates_from_folder(xml_folder_path=DEFAULT_OUTPUT_PATH):
    """
    Scan XML folder and extract existing dates from filenames

    Returns:
        set: Set of existing dates in YYYYMMDD format
    """
    xml_pattern = os.path.join(xml_folder_path, "*MGPPrezzi.xml")
    xml_files = glob.glob(xml_pattern)

    existing_dates = set()
    date_pattern = re.compile(r'(\d{8})MGPPrezzi\.xml$')

    for xml_file in xml_files:
        filename = os.path.basename(xml_file)
        match = date_pattern.search(filename)
        if match:
            existing_dates.add(match.group(1))

    return existing_dates

def get_missing_date_ranges(xml_folder_path=DEFAULT_OUTPUT_PATH, max_days_back=30):
    """
    Identify ALL missing date ranges from existing files to today+1 (including gaps)
    Let the server decide if data is available - we always try up to tomorrow

    Args:
        xml_folder_path: Path to XML folder
        max_days_back: Maximum days to look back if no files exist

    Returns:
        list: List of tuples (start_date, end_date) in YYYYMMDD format
    """
    existing_dates = get_existing_dates_from_folder(xml_folder_path)
    today = datetime.now()
    
    # Always check up to tomorrow - let the server tell us if data isn't ready yet
    end_check_date = today + timedelta(days=1)

    if not existing_dates:
        # No files exist, start from max_days_back ago
        start_date = end_check_date - timedelta(days=max_days_back)
        return [(start_date.strftime("%Y%m%d"), end_check_date.strftime("%Y%m%d"))]

    # Convert existing dates to set for faster lookup
    existing_date_strs = set(existing_dates)
    
    # Find oldest existing date to determine start point
    existing_datetimes = sorted([datetime.strptime(date_str, "%Y%m%d") for date_str in existing_dates])
    oldest_date = existing_datetimes[0]

    # Check every day from oldest to end_check_date and find gaps
    missing_ranges = []
    current_date = oldest_date
    
    while current_date.date() <= end_check_date.date():
        if current_date.strftime("%Y%m%d") not in existing_date_strs:
            # Found a missing date, find the end of this gap
            gap_start = current_date
            gap_end = current_date
            
            # Extend the gap to include consecutive missing dates
            next_date = current_date + timedelta(days=1)
            while (next_date.date() <= end_check_date.date() and 
                   next_date.strftime("%Y%m%d") not in existing_date_strs):
                gap_end = next_date
                next_date += timedelta(days=1)
            
            missing_ranges.append((gap_start.strftime("%Y%m%d"), gap_end.strftime("%Y%m%d")))
            current_date = next_date
        else:
            current_date += timedelta(days=1)

    return missing_ranges

def download_missing_gme_data(output_path=DEFAULT_OUTPUT_PATH, max_days_back=30):
    """
    Download only missing GME XML data based on existing files

    Args:
        output_path: Directory to save downloaded files
        max_days_back: Maximum days to look back if no files exist

    Returns:
        list: List of newly downloaded XML file paths
    """
    print("=== Smart GME Data Download ===")

    # Analyze existing files
    existing_dates = get_existing_dates_from_folder(output_path)
    missing_ranges = get_missing_date_ranges(output_path, max_days_back)

    print(f"Found {len(existing_dates)} existing files")
    if existing_dates:
        sorted_dates = sorted(existing_dates)
        print(f"Date range: {sorted_dates[0]} to {sorted_dates[-1]}")

    if not missing_ranges:
        print("No missing dates found - all data is up to date!")
        return []

    print(f"Missing date ranges: {missing_ranges}")

    all_downloaded_files = []

    # Download each missing range
    for start_date, end_date in missing_ranges:
        print(f"\nDownloading data from {start_date} to {end_date}...")

        # Calculate date_param (month before start_date)
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        date_param_dt = start_dt.replace(day=1).replace(month=start_dt.month-1) if start_dt.month > 1 else start_dt.replace(day=1).replace(month=12, year=start_dt.year-1)
        date_param = date_param_dt.strftime("%Y%m%d")

        # Use existing download function with specific date range
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Referer': 'https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download?valore=Prezzi',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'ModuleId': '12103',
            'TabId': '1749',
            'UserId': '-1'
        })

        # Get CSRF token
        try:
            page_response = session.get("https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download", timeout=10)
            if page_response.status_code == 200:
                csrf_match = re.search(r'<input[^>]*name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)["\']', page_response.text)
                csrf_token = csrf_match.group(1) if csrf_match else None
            else:
                csrf_token = None
        except Exception as e:
            print(f"Warning: Could not get CSRF token: {e}")
            csrf_token = None

        # Download parameters
        params = {
            'DataInizio': start_date,
            'DataFine': end_date,
            'Date': date_param,
            'Mercato': 'MGP',
            'Settore': 'Prezzi',
            'FiltroDate': 'InizioFine'
        }

        if csrf_token:
            params['__RequestVerificationToken'] = csrf_token

        try:
            url = "https://gme.mercatoelettrico.org/DesktopModules/GmeDownload/API/ExcelDownload/downloadzipfile"
            response = session.get(url, params=params, timeout=30)

            if response.status_code != 200:
                print(f"HTTP Error {response.status_code} for range {start_date}-{end_date}")
                continue

            # Extract XML files from ZIP
            os.makedirs(output_path, exist_ok=True)

            with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_ref:
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]

                for xml_file in xml_files:
                    xml_content = zip_ref.read(xml_file)
                    xml_filepath = os.path.join(output_path, xml_file)

                    # Only save if file doesn't exist (avoid overwriting)
                    if not os.path.exists(xml_filepath):
                        with open(xml_filepath, 'wb') as f:
                            f.write(xml_content)

                        all_downloaded_files.append(xml_filepath)
                        print(f"Downloaded: {xml_file} ({len(xml_content)} bytes)")
                    else:
                        print(f"Skipped existing: {xml_file}")

        except Exception as e:
            print(f"Error downloading range {start_date}-{end_date}: {e}")
            continue

    print(f"\nDownloaded {len(all_downloaded_files)} new files")
    return all_downloaded_files

def create_pun_csv_from_xml(xml_folder_path=DEFAULT_OUTPUT_PATH, output_filename="PUN_CM.csv"):
    """
    Create a CSV file with PUN hourly data from all XML files in the folder

    Args:
        xml_folder_path: Path to folder containing XML files
        output_filename: Name of output CSV file

    Returns:
        str: Path to created CSV file
    """

    # Find all XML files in the folder
    xml_pattern = os.path.join(xml_folder_path, "*.xml")
    xml_files = glob.glob(xml_pattern)

    if not xml_files:
        print(f"No XML files found in {xml_folder_path}")
        return None

    print(f"Found {len(xml_files)} XML files to process")

    # List to store all data
    all_data = []

    for xml_file in xml_files:
        try:
            print(f"Processing {os.path.basename(xml_file)}...")

            # Parse XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Extract data from each Prezzi element
            for prezzi in root.findall('Prezzi'):
                data_elem = prezzi.find('Data')
                ora_elem = prezzi.find('Ora')
                pun_elem = prezzi.find('PUN')

                if data_elem is not None and ora_elem is not None and pun_elem is not None:
                    # Convert PUN value from string with comma to float
                    pun_value = float(pun_elem.text.replace(',', '.'))

                    all_data.append({
                        'Data': data_elem.text,
                        'Ora': int(ora_elem.text),
                        'PUN': pun_value
                    })

        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
            continue

    if not all_data:
        print("No data extracted from XML files")
        return None

    # Create DataFrame and sort by Data and Ora
    df = pd.DataFrame(all_data)
    df = df.sort_values(['Data', 'Ora']).reset_index(drop=True)

    # Create output path
    csv_path = os.path.join(xml_folder_path, output_filename)

    # Save to CSV with semicolon separator
    df.to_csv(csv_path, index=False, sep=';')

    print(f"Created CSV with {len(df)} hourly records: {csv_path}")
    print(f"Data range: {df['Data'].min()} to {df['Data'].max()}")

    return csv_path

def update_csv_incremental(xml_folder_path=DEFAULT_OUTPUT_PATH, output_filename="PUN_CM.csv"):
    """
    Update CSV file incrementally with only new XML data

    Args:
        xml_folder_path: Path to folder containing XML files
        output_filename: Name of CSV file to update

    Returns:
        str: Path to updated CSV file
    """
    csv_path = os.path.join(xml_folder_path, output_filename)

    # Get XML files and their modification times
    xml_pattern = os.path.join(xml_folder_path, "*.xml")
    xml_files = glob.glob(xml_pattern)

    if not xml_files:
        print(f"No XML files found in {xml_folder_path}")
        return None

    # Check if CSV exists and get its modification time
    csv_exists = os.path.exists(csv_path)
    csv_mtime = os.path.getmtime(csv_path) if csv_exists else 0

    # Find XML files that are newer than the CSV
    new_xml_files = []
    for xml_file in xml_files:
        xml_mtime = os.path.getmtime(xml_file)
        if xml_mtime > csv_mtime:
            new_xml_files.append(xml_file)

    if not new_xml_files and csv_exists:
        print("CSV is up to date - no new XML files to process")
        return csv_path

    print(f"Processing {len(new_xml_files)} new/updated XML files")

    # Load existing CSV data if it exists
    existing_df = None
    existing_dates = set()

    if csv_exists:
        try:
            existing_df = pd.read_csv(csv_path)
            existing_dates = set(existing_df['Data'].astype(str))
            print(f"Loaded existing CSV with {len(existing_df)} records")
        except Exception as e:
            print(f"Error loading existing CSV: {e}")
            existing_df = None

    # Process only new XML files
    new_data = []
    for xml_file in new_xml_files:
        try:
            filename = os.path.basename(xml_file)
            print(f"Processing {filename}...")

            # Parse XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Extract data from each Prezzi element
            for prezzi in root.findall('Prezzi'):
                data_elem = prezzi.find('Data')
                ora_elem = prezzi.find('Ora')
                pun_elem = prezzi.find('PUN')

                if data_elem is not None and ora_elem is not None and pun_elem is not None:
                    date_str = data_elem.text

                    # Skip if this date already exists in CSV (avoid duplicates)
                    if existing_df is not None and date_str in existing_dates:
                        continue

                    # Convert PUN value from string with comma to float
                    pun_value = float(pun_elem.text.replace(',', '.'))

                    new_data.append({
                        'Data': date_str,
                        'Ora': int(ora_elem.text),
                        'PUN': pun_value
                    })

        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
            continue

    if not new_data and existing_df is not None:
        print("No new data to add")
        return csv_path

    # Create DataFrame with new data
    if new_data:
        new_df = pd.DataFrame(new_data)
        print(f"Extracted {len(new_df)} new records")

        # Combine with existing data if any
        if existing_df is not None:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        # Sort by Data and Ora
        combined_df = combined_df.sort_values(['Data', 'Ora']).reset_index(drop=True)

        # Remove duplicates (just in case)
        combined_df = combined_df.drop_duplicates(subset=['Data', 'Ora']).reset_index(drop=True)

    else:
        # No new data, just use existing
        combined_df = existing_df if existing_df is not None else pd.DataFrame()

    # Save updated CSV with semicolon separator
    combined_df.to_csv(csv_path, index=False, sep=';')

    print(f"Updated CSV with {len(combined_df)} total records: {csv_path}")
    if len(combined_df) > 0:
        # Convert Data column to string to ensure proper comparison
        combined_df['Data'] = combined_df['Data'].astype(str)
        print(f"Date range: {combined_df['Data'].min()} to {combined_df['Data'].max()}")

    return csv_path

if __name__ == "__main__":
    print("=== Smart GME Data Management System ===")

    # Step 1: Smart download (only missing data)
    result = download_missing_gme_data()

    # Step 2: Incremental CSV update (only process new files)
    print("\n=== Updating CSV incrementally ===")
    csv_path = update_csv_incremental()

    if csv_path:
        print(f"\n[SUCCESS] Electricity CSV updated: {os.path.basename(csv_path)}")

        # Show preview of CSV
        try:
            df_preview = pd.read_csv(csv_path)
            print(f"\nCSV Preview (last 5 rows):")
            print(df_preview.tail())
            print(f"\nTotal records: {len(df_preview)}")
        except Exception as e:
            print(f"Could not preview CSV: {e}")
    else:
        print("[FAILED] Electricity CSV update failed")
    
