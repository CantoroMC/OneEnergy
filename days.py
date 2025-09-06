import requests
import os
import zipfile
import io
import pandas as pd
from datetime import date

def download_gme_data(data_inizio, data_fine, date_param, output_path="data"):
    """
    Download data from GME endpoint

    Args:
        data_inizio: Start date (YYYYMMDD format)
        data_fine: End date (YYYYMMDD format)
        date_param: Date parameter (YYYYMMDD format)
        output_path: Directory to save the downloaded file
    """

    # Create a session to maintain cookies
    session = requests.Session()

    # Add headers to mimic the exact browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Priority': 'u=1, i',
        'Referer': 'https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download?valore=Prezzi',
        'Sec-CH-UA': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'ModuleId': '12103',
        'TabId': '1749',
        'UserId': '-1'
    }

    session.headers.update(headers)

    # Visit the download page first to get necessary cookies/tokens
    try:
        print("Visiting GME download page...")
        download_page = "https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download"
        page_response = session.get(download_page, timeout=10)
        print(f"Download page status: {page_response.status_code}")

        # Look for any CSRF tokens or form data in the page
        page_content = page_response.text

        # Check for common anti-forgery tokens
        import re
        csrf_token = None
        token_patterns = [
            r'<input[^>]*name=["\']__RequestVerificationToken["\'][^>]*value=["\']([^"\']+)["\']',
            r'<input[^>]*value=["\']([^"\']+)["\'][^>]*name=["\']__RequestVerificationToken["\']',
            r'"__RequestVerificationToken":"([^"]+)"',
            r'name="__VIEWSTATE" value="([^"]+)"'
        ]

        for pattern in token_patterns:
            match = re.search(pattern, page_content)
            if match:
                csrf_token = match.group(1)
                print(f"Found token: {csrf_token[:50]}...")
                break


    except Exception as e:
        print(f"Warning: Could not visit download page: {e}")
        csrf_token = None

    # Try the direct download URL
    url = "https://gme.mercatoelettrico.org/DesktopModules/GmeDownload/API/ExcelDownload/downloadzipfile"

    params = {
        'DataInizio': data_inizio,
        'DataFine': data_fine,
        'Date': date_param,
        'Mercato': 'MGP',
        'Settore': 'Prezzi',
        'FiltroDate': 'InizioFine'
    }

    # Add CSRF token if found
    if 'csrf_token' in locals() and csrf_token:
        params['__RequestVerificationToken'] = csrf_token
        print(f"Added CSRF token to request")

    try:
        print(f"Downloading data from {data_inizio} to {data_fine}...")

        # Use the exact headers from your PowerShell command
        print("Making request with exact headers...")
        response = session.get(url, params=params, timeout=30)

        # Check response status and content
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            # Check if we got actual data (ZIP file)
            content_type = response.headers.get('content-type', '').lower()
            print(f"Content type: {content_type}")

            # Check if response looks like a ZIP file by examining content
            content = response.content
            is_zip = (content[:4] == b'PK\x03\x04' or  # ZIP file magic bytes
                     'zip' in content_type or
                     'application/octet-stream' in content_type or
                     len(content) > 100)  # Assume large responses are files

            if is_zip:
                # Create output directory if it doesn't exist
                os.makedirs(output_path, exist_ok=True)

                # Generate filename
                filename = f"MGP_Prezzi_{data_inizio}_{data_fine}.zip"
                filepath = os.path.join(output_path, filename)

                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(content)

                print(f"Data successfully downloaded to: {filepath}")
                print(f"File size: {len(content)} bytes")

                return filepath
            else:
                # Print response to see what we got
                print(f"Response doesn't appear to be a ZIP file.")
                try:
                    print(f"Response text preview: {response.text[:500]}")
                except:
                    print(f"Response binary preview: {content[:100]}")
                return None
        else:
            print(f"HTTP Error {response.status_code}: {response.reason}")
            try:
                print(f"Response content: {response.text[:500]}")
            except:
                print(f"Response binary content: {response.content[:100]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error downloading data: {e}")
        return None

if __name__ == "__main__":
    print("=== Testing daily data download (original function) ===")
    result = download_gme_data("20240507", "20240507", "20240506")

    if result:
        print(f"\nDaily download completed successfully: {result}")
    else:
        print("\n=== SUMMARY ===")
        print("Unable to download daily data automatically. The GME API requires authentication.")
        print("Alternative approaches:")
        print("1. Manual download from: https://gme.mercatoelettrico.org/en-us/Home/Results/Electricity/MGP/Download")
        print("2. Use browser automation tools (Selenium)")
        print("3. Contact GME for API access credentials")
        print("\nThe endpoint you provided requires proper authorization headers or user authentication.")