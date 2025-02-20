from datetime import datetime
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time
import mysql.connector
from dotenv import load_dotenv
import os
import re
import platform
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Load environment variables from .env file
load_dotenv()

def extract_stock_data_api(url):
    # Make the GET request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Print the parsed data
        print(data)
        return data
    else:
        print(f"Request failed with status code {response.status_code}")
        return ""


def extract_stock_data(driver):
    """Extracts stock details from each card on the technical picks page."""
    try:
        # Wait for the elements to be present
        wait = WebDriverWait(driver, 10)
        cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".technical-picks-card")))
        stock_data = []
        print("Extracting stock data from cards :: " +str(cards.count()))
        
        for card in cards:
            # Extract stock name and other relevant details
            stock_details = {}

            try:
                stock_name_element = card.find_element(By.CSS_SELECTOR, ".stock-name")
                stock_details["stock_name"] = stock_name_element.text.strip()
            except Exception as e:
                print(f"Error extracting stock name: {e}")
                stock_details["stock_name"] = ""  # Handle missing details

            try:
                stock_code_element = card.find_element(By.CSS_SELECTOR, ".stock-code")
                stock_details["stock_code"] = stock_code_element.text.strip()
            except Exception as e:
                print(f"Error extracting stock code: {e}")
                stock_details["stock_code"] = ""

            try:
                recommendation_date_element = card.find_element(By.CSS_SELECTOR, ".recommendation-date")
                stock_details["recommendation_date"] = recommendation_date_element.text.strip()
            except Exception as e:
                print(f"Error extracting recommendation date: {e}")
                stock_details["recommendation_date"] = ""

            # Extract numerical data (prices) using more robust parsing
            for key in ["entry_price", "stoploss_price", "target_price", "current_price"]:
                try:
                    price_element = card.find_element(By.CSS_SELECTOR, f".{key.replace('_', '-')}")
                    price_text = price_element.text.strip()
                    price = float(re.sub(r"[^0-9.]", "", price_text))  # Remove non-numeric characters
                    stock_details[key] = price
                except Exception as e:
                    print(f"Error extracting {key}: {e}")
                    stock_details[key] = float('nan')  # Indicate missing data

            stock_data.append(stock_details)

        return stock_data
    except Exception as e:
        print(f"An error occurred while extracting stock data: {e}")
        return []




def login_and_extract_data(username, password,apiUrl):
    """Logs in to Moneycontrol and extracts stock data."""
    try:
        if platform.system() == "Windows":
            # Use Chrome on Windows
            driver = webdriver.Chrome(service=webdriver.ChromeService(ChromeDriverManager().install()))
            print("Using Chrome on Windows")
        elif platform.system() == "Linux":
            # Use Firefox on Linux (Ubuntu)
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            geckodriver_path = "/snap/bin/geckodriver"
            service = Service(geckodriver_path)
            driver = webdriver.Firefox(service=service, options=firefox_options)
            print("Using Firefox on Linux")
        else:
            print("Unsupported operating system.")
            return False

        # Navigate to the Moneycontrol login page
        driver.get("https://accounts.moneycontrol.com/mclogin/?v=2&d=2&cpurl=https://www.moneycontrol.com/")
        driver.maximize_window()
        try:
            # Attempt to find the "moneycontrol.com" link and click it if present.  This is a more robust check than just looking for the login button.
            moneycontrol_link = driver.find_elements(By.XPATH, "//a[@href='https://www.moneycontrol.com' and contains(text(), 'moneycontrol.com')]")
            if moneycontrol_link:
                moneycontrol_link[0].click()
        except Exception as e:
            print(f"Error clicking moneycontrol link: {e}")
            pass  # Proceed to the next step if the link is not found.


        wait = WebDriverWait(driver, 10)
        #login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='user_before_login blp']/a[@class='userlink']")))
        #login_button.click()
        # try:
        #     login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_signin.linkSignIn")))
        #     login_button.click()
        # except Exception as e:
        #     print(f"Error clicking login button: {e}")
        #     return False
        try:
            #driver.switch_to.frame(driver.find_element(By.ID, "myframe"))
            time.sleep(2)
            login_option = driver.find_elements(By.XPATH, "//div[@class='loginwithTab']/descendant::li[text()='Login with Password']")
            login_option[1].click()
            time.sleep(2)
            username_field = driver.find_elements(By.NAME, "email")
            password_field = driver.find_elements(By.NAME, "pwd")
            username_field[1].send_keys(username)
            password_field[1].send_keys(password)
            login_button = driver.find_elements(By.CSS_SELECTOR, "button.continue.login_verify_btn")
            login_button[0].click()
            time.sleep(5)
        except Exception as e:
            print(f"Error locating elements in login frame: {e}")
            return False
        # Wait for the technical picks page to load
        driver.get(apiUrl)
        json_response = driver.find_element(By.TAG_NAME, 'body').text
        driver.quit()
        # Parse the json into stockdata
        jsonData = json.loads(json_response)
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = connection.cursor()
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INT PRIMARY KEY,
            asset_class VARCHAR(255),
            instrument_type VARCHAR(255),
            instrument VARCHAR(255),
            reco_type VARCHAR(255),
            option_category VARCHAR(255),
            meta_data TEXT,
            reco_end_date DATETIME,
            updated_at DATETIME,
            created_at DATETIME,
            user_name VARCHAR(255),
            call_status VARCHAR(255),
            cmp VARCHAR(255),
            entry_condition VARCHAR(255),
            entry_price FLOAT,
            target_condition VARCHAR(255),
            target_price_1 FLOAT,
            stoploss_price FLOAT,
            target_return FLOAT,
            stoploss_condition VARCHAR(255),
            rationale TEXT,
            closed_on_dt DATETIME
        )
        ''')
        # Create portfolio table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INT PRIMARY KEY AUTO_INCREMENT,
            instrument VARCHAR(255),
            entry_price FLOAT,
            entry_date DATETIME,
            quantity INT,
            recommendation_id INT,
            buy_sell VARCHAR(255),
            FOREIGN KEY (recommendation_id) REFERENCES recommendations(id),
            current_price FLOAT,
            realized_profit FLOAT,
            exit_price FLOAT,
            exit_date DATETIME
        )
        ''')
        
        for item in jsonData['list']['data']:
            if item['instrument_type'] == 'cash' and item['asset_class'] == 'equity':
                insert_stock_data_to_db(item,cursor)
                connection.commit()
        #stock_data = extract_stock_data(driver)
        connection.close
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        if driver:
            driver.quit()
        return False


def insert_stock_data_to_db(stock_data,cursor):
    # Insert data if ID does not exist
    try:
        stock_data['reco_end_date'] = datetime.fromisoformat(stock_data['reco_end_date'].replace('Z', '+00:00'))
        stock_data['updated_at'] = datetime.fromisoformat(stock_data['updated_at'])
        stock_data['created_at'] = datetime.fromisoformat(stock_data['created_at'])
        stock_data['closed_on_dt'] = datetime.min if stock_data['closed_on_dt'] == "0001-11-30 00:00:00" else datetime.fromisoformat(stock_data['closed_on_dt'])
        cursor.execute('''SELECT id, call_status FROM recommendations WHERE id = %s''', (stock_data['id'],))
        result = cursor.fetchone()
        if result:
            existing_id = result[0]
            existing_call_status = result[1]
            if existing_call_status != stock_data['call_status']:
                # Update the recommendation table
                cursor.execute('''UPDATE recommendations SET call_status = %s WHERE id = %s''', (stock_data['call_status'], stock_data['id']))
                # Update the portfolio table (assuming selling)
                cursor.execute('''SELECT id FROM portfolio WHERE recommendation_id = %s''', (stock_data['id'],))
                portfolio_id_result = cursor.fetchone()
                if portfolio_id_result:
                    cursor.execute('''UPDATE portfolio SET exit_price = %s, exit_date = NOW() WHERE recommendation_id = %s''', (stock_data['cmp'], stock_data['id']))
            
            
        else:
            cursor.execute('''
            INSERT INTO recommendations (id, asset_class, instrument_type, instrument, reco_type, option_category, meta_data, reco_end_date, updated_at, created_at, user_name, call_status, cmp, entry_condition, entry_price, target_condition, target_price_1, stoploss_price, target_return, stoploss_condition, rationale, closed_on_dt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (stock_data['id'], stock_data['asset_class'], stock_data['instrument_type'], stock_data['instrument'], stock_data['reco_type'], stock_data['option_category'], stock_data['meta_data'], 
            stock_data['reco_end_date'], stock_data['updated_at'], stock_data['created_at'], stock_data['user_name'], stock_data['call_status'], stock_data['cmp'], stock_data['entry_condition'], 
            stock_data['entry_price'], stock_data['target_condition'], stock_data['target_price_1'], stock_data['stoploss_price'], stock_data['target_return'], stock_data['stoploss_condition'], 
            stock_data['rationale'], stock_data['closed_on_dt']))
            # Insert into portfolio table
            try:
                stock_data['meta_data'] = json.loads(stock_data['meta_data'])
                sc_symbol = stock_data['meta_data'].get('sc_symbol')
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for meta_data: {e}, stock_data: {stock_data}")
                sc_symbol = None
            if sc_symbol:
                stock_data['sc_symbol'] = sc_symbol
            else:
                stock_data['sc_symbol'] = None
            cursor.execute('''
            INSERT INTO portfolio (instrument, entry_price, entry_date, quantity, recommendation_id, buy_sell)
            VALUES (%s, %s, %s, 1, %s, 'buy')
            ''', (stock_data['sc_symbol'], stock_data['entry_price'],stock_data['created_at'], stock_data['id']))
        # Commit changes
        # connection.commit()
        
        # cursor.execute('''
        # INSERT INTO recommendations (id, asset_class, instrument_type, instrument, reco_type, option_category, meta_data, reco_end_date, updated_at, created_at, user_name, call_status, cmp, entry_condition, entry_price, target_condition, target_price_1, stoploss_price, target_return, stoploss_condition, rationale, closed_on_dt)
        # SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        # WHERE NOT EXISTS (SELECT 1 FROM recommendations WHERE id = %s)
        # ''', (stock_data['id'], stock_data['asset_class'], stock_data['instrument_type'], stock_data['instrument'], stock_data['reco_type'], stock_data['option_category'], stock_data['meta_data'], 
        # stock_data['reco_end_date'], stock_data['updated_at'], stock_data['created_at'], stock_data['user_name'], stock_data['call_status'], stock_data['cmp'], stock_data['entry_condition'], 
        # stock_data['entry_price'], stock_data['target_condition'], stock_data['target_price_1'], stock_data['stoploss_price'], stock_data['target_return'], stock_data['stoploss_condition'], 
        # stock_data['rationale'], stock_data['closed_on_dt'],stock_data['id']))

    except mysql.connector.Error as err:
        print(f"Error inserting data into database: {err}")

if __name__ == "__main__":
    username = os.getenv('MONEYCONTROL_USERNAME')
    password = os.getenv('MONEYCONTROL_PASSWORD')

    if username and password:
        if login_and_extract_data(username, password,"https://api.moneycontrol.com/mcapi/technicalpicks/recommendations?deviceType=I&version=150&start=0&limit=100&recommendation_type=active&asset_class=&instrument_type=&action_taken=&search=&analyst_id="):
            print("Data extraction and insertion completed successfully.")
    else:
        print("Username or password not found in .env file.")
