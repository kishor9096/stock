from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def max_pain(index):

	# Set up Firefox options
	firefox_options = Options()
	firefox_options.add_argument("--headless")  # Run in headless mode
	firefox_options.add_argument("--no-sandbox")
	firefox_options.add_argument("--disable-dev-shm-usage")

	# Set up the WebDriver
	geckodriver_path = "/snap/bin/geckodriver"  # Manually specify the path to geckodriver
	service = Service(geckodriver_path)
	driver = webdriver.Firefox(service=service, options=firefox_options)

	# Navigate to the Sensibull website
	url = "https://web.sensibull.com/futures-options-data?tradingsymbol="+index
	driver.get(url)

	# Example: Locate and extract data (modify selectors as needed)
	# Assuming we want to extract some data from the homepage
	try:
		# Wait for the element to be present
		wait = WebDriverWait(driver, 10)
		instrument_ltp_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//span[@class='instrument-ltp']")))
		if(instrument_ltp_element[0].text.strip() == "--"):
			time.sleep(2)
		instrument_ltp = instrument_ltp_element[0].text.strip()
		elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@dir='ltr']/descendant::button")))
		# iterate on each date button and if data-state="active" then fetch the max pain data else click on the button and then fetch the max pain data"
		for element in elements:
			if element.get_attribute("data-state") == "active":
				expiryDate = element.text
				print("Extracted Date:", expiryDate)
				element = wait.until(EC.presence_of_element_located((By.XPATH, "//p[text()='Max pain']/following-sibling::*")))
				data = element.text
				print("Extracted Data:", data)
				insert_data(expiryDate, data, index,instrument_ltp)
			else:
				element.click()
				time.sleep(2)
				expiryDate = element.text
				print("Extracted Date:", expiryDate)
				element = wait.until(EC.presence_of_element_located((By.XPATH, "//p[text()='Max pain']/following-sibling::*")))
				data = element.text
				print("Extracted Data:", data)
				insert_data(expiryDate, data, index,instrument_ltp)
	except Exception as e:
		print("An error occurred:", e)

	# Close the WebDriver
	driver.quit()

def insert_data(expiry_date, max_pain,index,instrument_ltp):
	try:
		# Convert expiry_date to DATE format
		#expiry_date = datetime.strptime(expiry_date, '%d-%b-%Y').date()
		
		connection = mysql.connector.connect(
			host=os.getenv('DB_HOST'),
			port=os.getenv('DB_PORT'),
			user=os.getenv('DB_USER'),
			password=os.getenv('DB_PASSWORD'),
			database=os.getenv('DB_NAME')
		)
		max_pain_price = max_pain.split("\n")[0].strip()
		max_pain_trend = max_pain.split("\n")[1].strip()
		index_price_close = instrument_ltp.strip()
		cursor = connection.cursor()
		query = "INSERT INTO max_pain_data (expiry_date, max_pain, index_name, index_price_close, max_pain_trend, max_pain_price) VALUES (%s, %s,%s,%s, %s,%s)"
		cursor.execute(query, (expiry_date, max_pain, index,index_price_close, max_pain_trend, max_pain_price))
		connection.commit()
		cursor.close()
		connection.close()
	except mysql.connector.Error as err:
		print("Error: {}".format(err))

if __name__ == "__main__":
	print("started : ", time.ctime())
	max_pain("NIFTY")
	print("ended : ", time.ctime())
	print("started : ", time.ctime())
	max_pain("BANKNIFTY")
	print("ended : ", time.ctime())
	print("started : ", time.ctime())
	max_pain("SENSEX")
	print("ended : ", time.ctime())
	print("started : ", time.ctime())
	max_pain("FINNIFTY")
	print("ended : ", time.ctime())
	print("started : ", time.ctime())
	max_pain("MIDCPNIFTY")
	print("ended : ", time.ctime())