# HIMSS Member Directory Scraper
A Python tool to automatically extract healthcare professional contact details from the HIMSS (Healthcare Information and Management Systems Society) Member Directory portal.

Project Overview
This project automates the extraction of professional information from the HIMSS Member Directory, which contains valuable healthcare industry contact data. The scraper handles authentication challenges, website navigation, and data extraction via a hybrid manual-automated approach.

Features  
✅ Authentication Handling: Works with Auth0-protected HIMSS portal

✅ Dynamic Content Navigation: Navigates through the Member Directory

✅ Pagination Support: Extracts data across all 200 directory pages

✅ Robust Data Extraction: Captures all profile fields from directory tables

✅ CSV Export: Saves extracted data in structured format for analysis

✅ Error Recovery: Handles connection issues and dynamic page elements

Requirements  
Python 3.8+

Google Chrome

Required Python packages (see requirements.txt)

Installation
bash
## Clone the repository
git clone https://github.com/your-username/himss-directory-scraper.git
cd himss-directory-scraper

## Install dependencies
pip install -r requirements.txt

## Create environment file with credentials
echo "HIMSS_USER=your.email@example.com" > .env
echo "HIMSS_PASS=your_password" >> .env
Usage
Step 1: Start Chrome with Remote Debugging
bash
## Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\ChromeSession

## macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=~/ChromeSession
Step 2: Manual Login & Navigation
Login to HIMSS using your credentials

Navigate to Member Directory (via Directories dropdown)

Leave browser window open with directory page displayed

Step 3: Run the Scraper
bash
python scraper.py
How It Works
The scraper operates in three main phases:

Connection Phase:

Connects to existing Chrome session with active HIMSS login

Verifies current page is Member Directory

Data Extraction Phase:

Parses table structure to extract member information

Processes multiple data types and formats

Pagination & Storage Phase:

Navigates through all directory pages (up to 200)

Stores collected data in CSV format

Implementation Details
Browser Control: Selenium WebDriver with Chrome

Authentication: Hybrid approach with manual login and automated session connection

Pagination Handling: JavaScript execution for reliable page transitions

Error Recovery: Exception handling with screenshots for troubleshooting

Challenges Overcome
Auth0 authentication detection avoidance

Dynamic content loading and pagination without URL changes

Table structure parsing with various data formats

Session management and state preservation

License
This project is licensed under the MIT License - see the LICENSE file for details.

Disclaimer
This tool is intended for educational purposes only. Users are responsible for complying with HIMSS terms of service when accessing their data.