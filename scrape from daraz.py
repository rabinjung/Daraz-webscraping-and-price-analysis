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
browser.get('https://www.daraz.com.np/')

input_search = browser.find_element(By.XPATH, '//*[@id="q"]')
search_button = browser.find_element(By.XPATH, "//*[@id='topActionHeader']/div[1]/div[2]/div/div[2]/form/div/div[2]/button")


input_search.send_keys("samsung phone")
search_button.click()




def get_next_iteration_number():
    historical_files = [file for file in os.listdir() if file.startswith('products_daraz_history_')]
    if historical_files:
        iterations = [int(file.split('_')[-1].split('.')[0]) for file in historical_files]
        next_iteration = max(iterations) + 1
    else:
        next_iteration = 1
    return next_iteration


def save_previous_data(previous_data, iteration):
    filename = f'products_daraz_history_{iteration}.json'
    with open(filename, 'w') as json_file:
        json.dump(previous_data, json_file)
    print(f"Previous data saved to {filename}")

try:
    with open('products_daraz.json', 'r') as json_file:
        previous_data = json.load(json_file)
    iteration = get_next_iteration_number()
    save_previous_data(previous_data, iteration)
except FileNotFoundError:
    print("No previous data found.")
    previous_data = []  

products_daraz = []

i = 1
while (i <= 20):
    print(f'Scraping page {i}')
    product_elements = browser.find_elements(By.XPATH, "//div[@class='gridItem--Yd0sa']")
    print(len(product_elements))  

    for product_element in product_elements:
        try:
            product_title = product_element.find_element(By.XPATH, './/div[@class="title-wrapper--IaQ0m"]').text
            product_link = product_element.find_element(By.XPATH, ".//a").get_attribute('href')
        except:
            print("No product found")
            break
        
        try:
            product_price_element = product_element.find_element(By.XPATH, './/div[@id="id-price"]//span[@class="currency--GVKjl"]')
            product_price = product_price_element.text

        except NoSuchElementException:
            print("Price not found for this product")
            product_price ="No price"
        except Exception as e:
            print(f"An error occurred while getting the price for '{product_title}': {str(e)}")
            product_price = "Error getting price"
            
        
        for prev_product in previous_data:
            if prev_product['title'] == product_title:
                prev_price = prev_product['price']
                if prev_price != "No price" and product_price != "No price" and product_price != "Error getting price":
                    try:
                        percentage_change = ((float(product_price.replace('Rs.', '').replace(',', '').strip()) - 
                                              float(prev_price.replace('Rs.', '').replace(',', '').strip())) / 
                                             float(prev_price.replace('Rs.', '').replace(',', '').strip())) * 100
                    except ValueError:
                        print(f"Error converting price to float for '{product_title}'")
                        percentage_change = None
                    break
        else:
            percentage_change = None
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        products_daraz.append({
            'title': product_title,
            'price': product_price,
            'url': product_link,
            'percentage_change': percentage_change,
            'scrape_time': current_time  
        })

    try:
        next_button = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//li[@title='Next Page']/a[@class='ant-pagination-item-link']")))
        next_button.click()
    except:
        print("Next page not found")
        break
    
    i += 1

with open('products_daraz.json', 'w') as json_file:
    json.dump(products_daraz, json_file)

print("Scraping finished. Data saved to 'products_daraz.json'")

browser.quit()
