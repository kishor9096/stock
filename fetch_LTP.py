import time
import os
from datetime import datetime
import mysql.connector
import dotenv
import requests
from bs4 import BeautifulSoup
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
# Load environment variables from .env file
dotenv.load_dotenv()

def update_stock_prices():
    """Connects to the MySQL database, fetches instrument names,
    gets latest prices, and updates the portfolio table.
    """
    try:
        if platform.system() == "Windows":
            # Use Chrome on Windows
            print("Using Chrome on Windows")
            driver = webdriver.Chrome(service=webdriver.ChromeService(ChromeDriverManager().install()))
            
        elif platform.system() == "Linux":
            # Use Firefox on Linux (Ubuntu)
            print("Using Firefox on Linux")
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            geckodriver_path = "/snap/bin/geckodriver"
            service = Service(geckodriver_path)
            driver = webdriver.Firefox(service=service, options=firefox_options)
            
        else:
            print("Unsupported operating system.")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    try:
        # Database connection details
        mydb = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        mycursor = mydb.cursor()

        # Replace 'your_query' with your actual query
        mycursor.execute("SELECT instrument FROM portfolio WHERE exit_date IS NULL")
        instruments = mycursor.fetchall()
    
        for instrument in instruments:
            instrument_name = instrument[0]
            # Replace 'your_price_fetching_logic' with your actual logic
            # Example using a hypothetical 'get_latest_price' function
            try:
                latest_price = get_latest_price(instrument_name,driver)
                if latest_price is not None:
                    update_query = f"UPDATE portfolio SET current_price = {latest_price} WHERE instrument = '{instrument_name}';"
                    mycursor.execute(update_query)
                    mydb.commit()
                    print(f"Updated price for {instrument_name} to {latest_price}")
                else:
                    print(f"Could not fetch price for {instrument_name}")
            except Exception as e:
                print(f"Error updating price for {instrument_name}: {e}")

        mydb.close()

    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL database: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if driver:
            driver.quit()


def get_latest_price(instrument_name,driver):
    """
    Replace this with your actual logic to fetch the latest price
    for the given instrument.  This is a placeholder.
    """
    try:
        url = f"https://www.tradingview.com/symbols/NSE-{instrument_name}/"
        driver.get(url)
        driver.maximize_window()
        time.sleep(2)
        price_element = driver.find_elements(By.XPATH, "//div[contains(@class, 'symbol-header-ticker')]//descendant::span[contains(@class, 'symbol-last')]")

        if price_element:
            try:
                latest_price = float(price_element[0].text.replace(",", ""))
            except:
                driver.get(url)
                time.sleep(5)
                price_element = driver.find_elements(By.XPATH, "//div[contains(@class, 'symbol-header-ticker')]//descendant::span[contains(@class, 'symbol-last')]")
                latest_price = float(price_element[0].text.replace(",", ""))
            return latest_price
        else:
            print(f"Could not find price element for {instrument_name} on TradingView.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price from TradingView for {instrument_name}: {e}")
        return None
    except (ValueError, AttributeError) as e:
        print(f"Error parsing price for {instrument_name}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching price for {instrument_name}: {e}")
        return None


def update_stock_exit_date():
    mydb = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    mycursor = mydb.cursor()

    try:
        mycursor.execute("SELECT id, instrument,current_price,entry_price,quantity FROM portfolio WHERE exit_date IS NULL")
        stocks_to_check = mycursor.fetchall()

        for (portfolio_id, instrument_name,ltp,entry_price,quantity) in stocks_to_check:
            try:
                mycursor.execute("SELECT target_price_1, stoploss_price FROM recommendations WHERE id = (SELECT recommendation_id FROM portfolio WHERE id = %s)", (portfolio_id,))
                recommendation_data = mycursor.fetchone()

                if recommendation_data:
                    target_price = recommendation_data[0]
                    stoploss_price = recommendation_data[1]
                    latest_price = ltp

                    if latest_price is not None:
                        profit = (latest_price - entry_price)*quantity

                        if target_price and latest_price >= target_price:
                            print(f"Target price reached for {instrument_name} (portfolio_id: {portfolio_id}). Updating exit_date.")
                            mycursor.execute("UPDATE portfolio SET exit_date = %s, exit_price = %s, realized_profit = %s WHERE id = %s", (datetime.now(), latest_price, profit, portfolio_id))
                            mydb.commit()
                        elif stoploss_price and latest_price <= stoploss_price:
                            print(f"Stop loss triggered for {instrument_name} (portfolio_id: {portfolio_id}). Updating exit_date.")
                            mycursor.execute("UPDATE portfolio SET exit_date = %s, exit_price = %s, realized_profit = %s WHERE id = %s", (datetime.now(), latest_price, profit, portfolio_id))
                            mydb.commit()
                    else:
                        print(f"Could not fetch latest price for {instrument_name}. Skipping.")
            except mysql.connector.Error as e:
                print(f"Error updating portfolio data for {instrument_name}: {e}")
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)



if __name__ == "__main__":
    update_stock_prices()
    update_stock_exit_date()
