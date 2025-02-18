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

# Load environment variables from .env file
load_dotenv()

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


def login_and_extract_data(username, password):
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
        driver.get("https://www.moneycontrol.com/")
        login_button = driver.find_element(By.XPATH, "//div[@class='user_before_login blp']/a[@class='userlink']")
        login_button.click()
        time.sleep(2) #Added a small delay to ensure page load
        

        # Find and fill login form fields (adjust selectors as needed)
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        wait = WebDriverWait(driver, 10)
        try:
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_signin.linkSignIn")))
            login_button.click()
        except Exception as e:
            print(f"Error clicking login button: {e}")
            return False

        time.sleep(2)  #Added a small delay to ensure page load
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@class='signup_ctc' and @data-target='#mc_login']")))
        login_button.click()
        time.sleep(2) #Added a small delay to ensure page load

        # Find and fill login form fields (adjust selectors as needed)
        username_field = driver.find_element(By.Name, "email")
        password_field = driver.find_element(By.Name, "pwd")
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button = driver.find_element(By.XPATH, "//button[@type='button' and @class='continue login_verify_btn']")
        login_button.click()
        #Added wait to ensure page load
        time.sleep(5)
        
        # Wait for the technical picks page to load
        driver.get("https://www.moneycontrol.com/technical-picks/")
        time.sleep(5)  # Add a delay to allow page to load

        stock_data = extract_stock_data(driver)

        # Insert data into the database
        insert_stock_data_to_db(stock_data)

        driver.quit()
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        if driver:
            driver.quit()
        return False


def insert_stock_data_to_db(stock_data):
    """Inserts stock data into the MySQL database.  Updates the table schema."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = connection.cursor()

        # Create table if it doesn't exist, or update the schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stock_name VARCHAR(255),
                stock_code VARCHAR(255),
                recommendation_date DATE,
                entry_price DECIMAL(10, 2),
                stoploss_price DECIMAL(10, 2),
                target_price DECIMAL(10, 2),
                current_price DECIMAL(10, 2),
                source VARCHAR(255) DEFAULT 'Other'
            )
        """)

        for stock in stock_data:
            values = (
                stock.get('stock_name', ''),
                stock.get('stock_code', ''),
                stock.get('recommendation_date', None),
                stock.get('entry_price', float('nan')),
                stock.get('stoploss_price', float('nan')),
                stock.get('target_price', float('nan')),
                stock.get('current_price', float('nan'))
            )
            cursor.execute("""
                INSERT INTO stock_data (stock_name, stock_code, recommendation_date, entry_price, stoploss_price, target_price, current_price, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, values + ('MoneyControl',))  # Add 'MoneyControl' as the source

        connection.commit()
        cursor.close()
        connection.close()
        print("Stock data inserted successfully.")

    except mysql.connector.Error as err:
        print(f"Error inserting data into database: {err}")

if __name__ == "__main__":
    username = os.getenv('MONEYCONTROL_USERNAME')
    password = os.getenv('MONEYCONTROL_PASSWORD')

    if username and password:
        if login_and_extract_data(username, password):
            print("Data extraction and insertion completed successfully.")
    else:
        print("Username or password not found in .env file.")
