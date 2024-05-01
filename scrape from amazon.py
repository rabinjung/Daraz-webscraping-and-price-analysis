import json
import os
from datetime import datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


browser = webdriver.Chrome()
browser.get('https://www.amazon.in')


input_search = browser.find_element(By.ID, 'twotabsearchtextbox')
search_button = browser.find_element(By.XPATH, "(//input[@type='submit'])[1]")


input_search.send_keys("samsung phone")
search_button.click()



def get_next_iteration_number():
    historical_files = [file for file in os.listdir() if file.startswith('products_amazon_history_')]
    if historical_files:
        iterations = [int(file.split('_')[-1].split('.')[0]) for file in historical_files]
        next_iteration = max(iterations) + 1
    else:
        next_iteration = 1
    return next_iteration

def save_previous_data(previous_data, iteration):
    filename = f'products_amazon_history_{iteration}.json'
    with open(filename, 'w') as json_file:
        json.dump(previous_data, json_file)
    print(f"Previous data saved to {filename}")

try:
    with open('products_amazon.json', 'r') as json_file:
        previous_data = json.load(json_file)
    iteration = get_next_iteration_number()
    save_previous_data(previous_data, iteration)
except FileNotFoundError:
    print("No previous data found.")

products = []

i = 1
while i <= 15:
    print(f'Scraping page {i}')
    product_elements = browser.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")
    print(len(product_elements))
    
    for product_element in product_elements:
        try:
            product_link = product_element.find_element(By.XPATH, ".//a[@class='a-link-normal s-no-outline']").get_attribute('href')
            product_title = product_element.find_element(By.XPATH, ".//span[@class='a-size-medium a-color-base a-text-normal']").text
        except NoSuchElementException:
            print("Product not available")
            break
        
        try:
            product_price_element = product_element.find_element(By.XPATH, ".//span[@class='a-price']//span[@class='a-price-whole']")
            product_price = product_price_element.text
        except NoSuchElementException:
            product_price = "Price not available"
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for prev_product in previous_data:
            if prev_product['title'] == product_title:
                prev_price = prev_product['price']
                if prev_price != "Price not available" and product_price != "Price not available":
                    percentage_change = ((float(product_price.replace(',', '')) - 
                                          float(prev_price.replace(',', ''))) / 
                                         float(prev_price.replace(',', ''))) * 100
                    break
        else:
            percentage_change = None
        
        products.append({
            'title': product_title,
            'url': product_link,
            'price': product_price,
            'percentage_change': percentage_change,
            'scrape_time': current_time  
        })
        
    try:
        next_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[text()='Next']"))
        )
        next_button.click()
    except:
        print("Next page not found")
        break
    sleep(2)
    i += 1

with open('products_amazon.json', 'w') as json_file:
    json.dump(products, json_file)

print("Scraping finished. Data saved to 'products_amazon.json'.")
