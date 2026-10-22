from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1600,1200')
driver = webdriver.Chrome(options=options)
try:
    driver.get('http://localhost:8501')
    time.sleep(6)
    elems = driver.find_elements(By.XPATH, '//*[contains(text(), "Core Contribution")]')
    for el in elems:
        print('Tag:', el.tag_name, 'Parent:', el.find_element(By.XPATH, '..').tag_name, 'Classes:', el.get_attribute('class'))
except Exception as e:
    print('Error:', e)
finally:
    driver.quit()
