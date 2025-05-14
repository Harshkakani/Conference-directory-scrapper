from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import csv
import time
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("himss_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HimssDirectoryScraper:
    def __init__(self, username, password, output_file="himss_directory.csv"):
        """Initialize the scraper with login credentials and output file."""
        self.username = username
        self.password = password
        self.output_file = output_file
        self.login_url = "https://myportal.himss.org/s/login"
        self.directory_url = "https://myportal.himss.org/s/membershipdirectory?id=a6nRl000000EAh3"
        self.data = []
        
        # Set up screenshot directory
        os.makedirs("screenshots", exist_ok=True)
        
        # Configure Chrome options - FIXED FOR SELENIUM 4
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors=yes")
        
        # Initialize WebDriver with fixed initialization for Selenium 4
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options  # Only using options, no desired_capabilities
        )
        self.driver.set_page_load_timeout(90)  # Increased timeout for page loading
        
    def login_with_auto_detection(self):
        """Handle login process with automatic detection of success"""
        try:
            logger.info("Starting login process")
            self.driver.get(self.login_url)
            self.driver.save_screenshot("screenshots/login_page_initial.png")
            
            try:
                # Find and fill username/email field
                username_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "emailinput"))
                )
                username_field.clear()
                username_field.send_keys(self.username)
                logger.info("Entered username in standard form")
                
                # Find and fill password field
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(self.password)
                logger.info("Entered password in standard form")
                
                # Click login button
                login_button = self.driver.find_element(By.ID, "btn-login")
                self.driver.save_screenshot("screenshots/before_login_submit.png")
                login_button.click()
                logger.info("Clicked login button on standard form")
                
            except Exception as e:
                logger.warning(f"Failed to automate standard login: {str(e)}")
                logger.warning("*** MANUAL ACTION REQUIRED: Please complete the login form manually ***")
            
            # Display message about CAPTCHA/manual verification
            logger.info("If CAPTCHA is present or additional verification is required, please complete it manually")
            logger.info("Waiting for successful login detection (max 3 minutes)...")
            
            # Wait for signs of successful login
            WebDriverWait(self.driver, 180).until(
                lambda driver: any([
                    "myportal.himss.org/s/" in driver.current_url,
                    len(driver.find_elements(By.XPATH, "//a[contains(text(), 'Directories')]")) > 0,
                    len(driver.find_elements(By.XPATH, "//div[contains(text(), 'My Info')]")) > 0
                ])
            )
            
            # Add delay after login detection to let session establish
            time.sleep(8)
            self.driver.save_screenshot("screenshots/post_login.png")
            logger.info("Login successful - session established")
            return True
            
        except Exception as e:
            logger.error(f"Login process failed: {str(e)}")
            self.driver.save_screenshot("screenshots/login_failure.png")
            return False
            
    def navigate_to_directory(self):
        """Navigate to directory via UI elements using exact HTML structure"""
        try:
            logger.info("Attempting UI navigation to directory...")
            # First make sure we're on the main portal page
            self.driver.get("https://myportal.himss.org/s/")
            time.sleep(5)
            
            # Click on Directories in the top navigation - using exact match from screenshot
            directories_link = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Directories']"))
            )
            logger.info("Found Directories link, clicking...")
            directories_link.click()
            time.sleep(5)
            
            # Look for Membership Directory link
            membership_links = self.driver.find_elements(By.XPATH, 
                "//a[contains(text(), 'Membership Directory') or contains(text(), 'Corporate Membership')]")
            
            if membership_links:
                logger.info("Found Membership Directory link, clicking...")
                membership_links[0].click()
                time.sleep(8)  # Wait longer for page to load
                
                # Verify directory page loaded
                if len(self.driver.find_elements(By.XPATH, "//a[text()='Go to Site']")) > 0:
                    logger.info("Successfully reached directory page via UI navigation")
                    return True
                else:
                    logger.warning("Navigation succeeded but directory page elements not found")
                    return False
            else:
                logger.warning("Could not find Membership Directory link")
                return False
                
        except Exception as e:
            logger.error(f"UI navigation failed: {str(e)}")
            self.driver.save_screenshot("screenshots/ui_navigation_error.png")
            return False
    
    def extract_company_data(self):
        """Extract company data based on the exact HTML structure provided"""
        try:
            logger.info("Starting data extraction using provided HTML structure")
            
            # Wait for company containers to load using the fonteva-record class from HTML
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'fonteva-record')]"))
            )
            
            # Find all company containers
            company_containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'fonteva-record')]")
            logger.info(f"Found {len(company_containers)} company entries on current page")
            
            page_data = []
            for container in company_containers:
                try:
                    # Extract company name using the slds-text-heading_x-small class from the HTML
                    name_element = container.find_element(By.XPATH, ".//div[contains(@class, 'slds-text-heading_x-small')]")
                    company_name = name_element.text.strip()
                    
                    # Extract state using the slds-text-color--gray class and United States text from HTML
                    state_element = container.find_element(By.XPATH, ".//div[contains(@class, 'slds-text-color--gray') and contains(text(), 'United States')]")
                    state_code = state_element.text.split("United States")[0].strip()
                    
                    # Extract website URL from the Go to Site link
                    url_element = container.find_element(By.XPATH, ".//a[text()='Go to Site']")
                    website_url = url_element.get_attribute("href")
                    
                    company_data = {
                        "Company Name": company_name,
                        "State": state_code,
                        "Website URL": website_url
                    }
                    
                    page_data.append(company_data)
                    logger.info(f"Extracted: {company_name} ({state_code})")
                    
                except Exception as e:
                    logger.warning(f"Error extracting data from company container: {str(e)}")
            
            # Add to overall data collection
            self.data.extend(page_data)
            
            # Save current page data
            self.save_to_csv(f"himss_directory_page_{self._get_current_page()}.csv", page_data)
            
            logger.info(f"Successfully extracted {len(page_data)} companies from current page")
            return True
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            self.driver.save_screenshot("screenshots/extraction_error.png")
            return False
    
    def handle_pagination(self):
        """Handle pagination using the exact HTML structure provided"""
        try:
            # Get total pages
            total_pages = self._get_total_pages()
            logger.info(f"Found {total_pages} total pages to scrape")
            
            current_page = 1
            while current_page <= total_pages:
                logger.info(f"Processing page {current_page} of {total_pages}")
                
                # Extract data from current page
                self.extract_company_data()
                
                # Check if we're on the last page
                if current_page >= total_pages:
                    break
                    
                # Go to next page using the title attribute from HTML
                if not self._go_to_next_page():
                    logger.warning("Failed to navigate to next page")
                    break
                    
                current_page += 1
                
            return True
            
        except Exception as e:
            logger.error(f"Pagination handling failed: {str(e)}")
            return False
    
    def _get_total_pages(self):
        """Get total page count from pagination section using exact HTML structure"""
        try:
            # Using the HTML structure provided, get text from the span following "of"
            total_pages_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'of')]/following-sibling::span"))
            )
            total_pages = int(total_pages_element.text.strip())
            logger.info(f"Total pages: {total_pages}")
            return total_pages
        except Exception as e:
            logger.warning(f"Could not determine total pages: {str(e)}")
            return 1  # Default to 1 if we can't find pagination
    
    def _get_current_page(self):
        """Get current page number from the input field"""
        try:
            # Using the uiInputSmartNumber class from HTML structure
            current_page_input = self.driver.find_element(By.XPATH, "//input[contains(@class, 'uiInputSmartNumber')]")
            current_page = int(current_page_input.get_attribute("value"))
            return current_page
        except:
            return 1  # Default to page 1
    
    def _go_to_next_page(self):
        """Click the Next Page button using the HTML structure provided"""
        try:
            # Find Next Page button using title attribute from the HTML
            next_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='Next Page']"))
            )
            
            # Check if button is enabled
            if not next_button.is_enabled():
                logger.info("Next button is disabled - reached the last page")
                return False
                
            # Get current page for verification
            current_page = self._get_current_page()
            
            # Take screenshot before clicking
            self.driver.save_screenshot(f"screenshots/before_next_page_{current_page}.png")
            
            # Click the button
            next_button.click()
            logger.info(f"Clicked Next Page button from page {current_page}")
            
            # Wait for page to refresh and verify page number increased
            time.sleep(5)
            new_page = self._get_current_page()
            
            if new_page > current_page:
                logger.info(f"Successfully navigated to page {new_page}")
                return True
            else:
                logger.warning(f"Page number did not change after clicking Next (still {current_page})")
                return False
                
        except Exception as e:
            logger.error(f"Next page navigation failed: {str(e)}")
            self.driver.save_screenshot("screenshots/next_page_error.png")
            return False
    
    def save_to_csv(self, filename=None, data_to_save=None):
        """Save the scraped data to a CSV file."""
        if filename is None:
            filename = self.output_file
            
        if data_to_save is None:
            data_to_save = self.data
            
        try:
            if not data_to_save:
                logger.warning(f"No data to save to {filename}")
                return False
                
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Company Name", "State", "Website URL"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data_to_save:
                    writer.writerow(row)
                    
            logger.info(f"Successfully saved {len(data_to_save)} records to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data to CSV: {str(e)}")
            return False
    
    def run(self):
        """Run the complete scraping process"""
        try:
            logger.info("Starting HIMSS directory scraper")
            
            # Login to the portal
            if not self.login_with_auto_detection():
                logger.error("Login failed. Cannot proceed with scraping.")
                return False
                
            # Navigate to directory
            if not self.navigate_to_directory():
                logger.error("Directory navigation failed. Cannot proceed with scraping.")
                return False
                
            # Handle pagination and extract data from all pages
            if not self.handle_pagination():
                logger.warning("Issues occurred during pagination and data extraction.")
                
            # Save final consolidated data to CSV
            if self.data:
                self.save_to_csv()
                logger.info(f"All data successfully saved to {self.output_file}")
            else:
                logger.warning("No data was collected during scraping.")
                
            logger.info("Scraping process completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during scraping process: {str(e)}")
            return False
            
        finally:
            # Clean up
            self.driver.quit()
            logger.info("Browser closed")

def main():
    """Main function to run the scraper."""
    # Replace with your HIMSS login credentials
    username = "aditya.hanchinal@utdallas.edu"
    password = "Student@2025"
    
    # Create and run the scraper
    scraper = HimssDirectoryScraper(username, password)
    scraper.run()
    
if __name__ == "__main__":
    main()
