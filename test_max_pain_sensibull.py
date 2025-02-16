# tests/test_max_pain_sensibull.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

def test_webdriver_setup():
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # Run in headless mode
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")
    geckodriver_path = "/snap/bin/geckodriver"
    service = Service(geckodriver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)
    driver.quit()