# scraper.py
import os
import time
import random
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Load environment variables
load_dotenv('.env')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def login(driver):
    """Handle login with correct form element IDs"""
    try:
        print("Navigating to HIMSS homepage...")
        driver.get("https://www.himss.org/")

        # Wait for page to load completely
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Click login button
        print("Locating login button...")
        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "li.mega-menu__login > button#login")
            )
        )

        print("Clicking login button...")
        driver.execute_script("arguments[0].click();", login_button)

        # Wait for login form to load - using correct ID selector
        print("Waiting for login form...")
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "emailinput"))
        )

        # Enter credentials using correct ID selectors
        print("Entering email...")
        driver.find_element(By.ID, "emailinput").send_keys(os.getenv('HIMSS_USER'))
        
        print("Entering password...")
        driver.find_element(By.ID, "password").send_keys(os.getenv('HIMSS_PASS'))
        
        # Click sign in button using correct ID
        print("Clicking sign in button...")
        driver.find_element(By.ID, "btn-login").click()

        # Verify successful login
        WebDriverWait(driver, 30).until(
            EC.url_contains("myportal.himss.org/s/")
        )
        print("Login successful!")
        return True

    except Exception as e:
        print(f"Login failed: {str(e)}")
        driver.save_screenshot("login_failure.png")
        return False

def navigate_to_directory(driver):
    """Directory navigation with fallback"""
    try:
        driver.get("https://myportal.himss.org/s/membershipdirectory")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.slds-table"))
        )
        return True
    except:
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Directories"))
            ).click()
            
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Member Directory"))
            ).click()
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            return True
        except Exception as e:
            print(f"Navigation failed: {str(e)}")
            return False

def extract_table_data(driver):
    """Data extraction from table"""
    try:
        table = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "table.slds-table"))
        )
        headers = [header.get_attribute("title") for header in table.find_elements(By.CSS_SELECTOR, "th.slds-cell-wrap")]
        rows = table.find_elements(By.CSS_SELECTOR, "tr.fonteva-record")
        
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells) if i < len(headers)}
            data.append(row_data)
        return data
    except Exception as e:
        print(f"Data extraction error: {str(e)}")
        return []

def handle_pagination(driver):
    """Pagination handling"""
    try:
        current_page = driver.find_element(
            By.CSS_SELECTOR, 
            "div.slds-grid.slds-grid--align-center"
        ).text
        
        next_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Next Page']"))
        )
        next_btn.click()
        
        WebDriverWait(driver, 15).until_not(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, "div.slds-grid.slds-grid--align-center"), 
                current_page
            )
        )
        return True
    except Exception as e:
        print(f"Pagination error: {str(e)}")
        return False

def main():
    driver = setup_driver()
    try:
        if not login(driver):
            raise RuntimeError("Login failed after 3 attempts")
            
        if not navigate_to_directory(driver):
            raise RuntimeError("Directory access failed")
            
        all_data = []
        current_page = 1
        max_pages = 2  # Start with 2 pages for testing
        
        while current_page <= max_pages:
            print(f"Processing page {current_page}")
            page_data = extract_table_data(driver)
            all_data.extend(page_data)
            
            if not handle_pagination(driver) or current_page == max_pages:
                break
                
            current_page += 1
            time.sleep(random.uniform(1, 3))  # Random delay
            
        if all_data:
            pd.DataFrame(all_data).to_csv("himss_members.csv", index=False)
            print(f"Saved {len(all_data)} records")
        else:
            print("No data collected")
            
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        driver.save_screenshot("error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
