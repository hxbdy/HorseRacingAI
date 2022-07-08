# Selenium https://www.selenium.dev/ja/documentation/webdriver/getting_started/install_drivers/
# Use Webdriver Manager for Python: https://github.com/SergeyPirogov/webdriver_manager

# Import code:
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Use the `install()` method to set `executabe_path` in a new `Service` instance:
service = Service(executable_path=ChromeDriverManager().install())

# Pass in the `Service` instance with the `service` keyword: 
driver = webdriver.Chrome(service=service)
