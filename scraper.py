# scraper.py
import os
import time
import random
import html
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def connect_to_existing_chrome():
    """Connect to an existing Chrome session with remote debugging enabled"""
    print("Connecting to existing Chrome session...")
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        print(f"Connected to Chrome. Current URL: {driver.current_url}")
        return driver
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return None

def extract_table_data(driver):
    """Extract data directly from visible table"""
    try:
        # Wait for table to load completely
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        time.sleep(1)  # Give table a moment to stabilize
        
        # Get all visible header cells
        headers = []
        header_cells = driver.find_elements(By.CSS_SELECTOR, "table th")
        for header in header_cells:
            header_text = header.text.strip()
            if header_text:
                headers.append(header_text)
        
        print(f"Found {len(headers)} columns")
        if len(headers) == 0:
            print("Warning: No headers found, checking for alternative header structure")
            header_cells = driver.find_elements(By.CSS_SELECTOR, ".tableHeaders")
            headers = [h.get_attribute("title") for h in header_cells]
            print(f"Found {len(headers)} columns with alternative selector")
        
        # Get all visible rows
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"Found {len(rows)} rows")
        
        data = []
        for row in rows:
            # Get all cells in current row
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 2:  # Skip rows with insufficient cells
                continue
                
            # Extract text directly from each cell
            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row_data[headers[i]] = cell.text.strip()
            
            if any(row_data.values()):  # Only add rows with data
                data.append(row_data)
        
        print(f"Extracted {len(data)} records")
        return data
    
    except Exception as e:
        print(f"Extraction error: {str(e)}")
        driver.save_screenshot(f"extraction_error_{int(time.time())}.png")
        return []

def handle_pagination(driver, max_retries=3):
    """Simple pagination handler that works with the page's structure"""
    for retry in range(max_retries):
        try:
            # Get the current page content signature for comparison
            current_table_state = driver.find_element(By.TAG_NAME, "tbody").get_attribute("innerHTML")
            
            # Find the next button directly by its title attribute
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Next Page']"))
            )
            
            if "disabled" in next_btn.get_attribute("class"):
                print("Next button is disabled - reached last page")
                return False
            
            print(f"Clicking next page button (attempt {retry+1})...")
            driver.execute_script("arguments[0].click();", next_btn)
            
            # Wait for table content to change (most reliable indicator)
            WebDriverWait(driver, 15).until(
                lambda d: d.find_element(By.TAG_NAME, "tbody").get_attribute("innerHTML") != current_table_state
            )
            
            # Additional verification that data loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr"))
            )
            
            # Allow time for any animations to complete
            time.sleep(2)
            print("Successfully navigated to next page")
            return True
            
        except Exception as e:
            print(f"Pagination error (attempt {retry+1}): {str(e)}")
            driver.save_screenshot(f"pagination_error_{retry+1}.png")
            time.sleep(2)
    
    return False

def main():
    """Main execution flow"""
    driver = connect_to_existing_chrome()
    if not driver:
        print("Failed to connect to Chrome. Make sure Chrome is running with remote debugging on port 9222.")
        return
        
    try:
        all_data = []
        current_page = 1
        max_pages = 200
        
        while current_page <= max_pages:
            print(f"\nProcessing page {current_page} of {max_pages}")
            page_data = extract_table_data(driver)
            
            if page_data:
                all_data.extend(page_data)
                print(f"Total records collected so far: {len(all_data)}")
            else:
                print("No data found on current page")
                break
                
            if current_page == max_pages:
                print(f"Reached configured limit of {max_pages} pages")
                break
                
            if not handle_pagination(driver):
                print("No more pages available or pagination failed")
                break
                
            current_page += 1
            time.sleep(random.uniform(2.0, 3.0))
        
        # Save the collected data
        if all_data:
            df = pd.DataFrame(all_data)
            output_file = "himss_members.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Successfully saved {len(all_data)} records to {output_file}")
        else:
            print("No data was collected")
            
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        driver.save_screenshot(f"fatal_error_{int(time.time())}.png")
        
    print("Script execution complete")

if __name__ == "__main__":
    main()
