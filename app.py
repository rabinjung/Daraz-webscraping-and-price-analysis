from flask import Flask, request, render_template
import json
import os
from datetime import datetime
import plotly.graph_objs as go

app = Flask(__name__)

with open('products_daraz.json', 'r') as daraz_file:
    daraz_products = json.load(daraz_file)

with open('products_amazon.json', 'r') as amazon_file:
    amazon_products = json.load(amazon_file)

def find_similar_products(product_name, products, threshold=20):
    similar_products = []
    for product in products:
        if product_name[:threshold].lower() in product['title'].lower():
            similar_products.append(product)
    return similar_products

def get_product_history_filename(product_source):
    if product_source == 'daraz':
        return 'products_daraz_history_'
    elif product_source == 'amazon':
        return 'products_amazon_history_'
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query'].lower() 
    daraz_results = find_similar_products(query, daraz_products)
    amazon_results = find_similar_products(query, amazon_products)
    return render_template('search_results.html', daraz_results=daraz_results, amazon_results=amazon_results)

@app.route('/show_graph', methods=['POST'])
def show_graph():
    product_source = request.form['product_source']
    product_name = request.form['product_name'].lower()

    product_history_prefix = get_product_history_filename(product_source)

    if product_history_prefix:
        similar_products = find_similar_products(product_name, daraz_products if product_source == 'daraz' else amazon_products)

        if similar_products:
            suggested_product_names = [product['title'] for product in similar_products]
            return render_template('select_product.html', product_source=product_source, suggested_product_names=suggested_product_names)
        else:
            return "No similar products found"
    else:
        return "Invalid product source"

@app.route('/plot_graph', methods=['POST'])
def plot_graph():
    product_source = request.form['product_source']
    selected_product_name = request.form['selected_product']

    product_history_prefix = get_product_history_filename(product_source)

    if product_history_prefix:
        products = daraz_products if product_source == 'daraz' else amazon_products

        selected_product = next((product for product in products if product['title'].lower() == selected_product_name.lower()), None)

        if selected_product:
            prices = []
            scrape_dates = []
            for file in os.listdir():
                if file.startswith(product_history_prefix):
                    with open(file, 'r') as json_file:
                        data = json.load(json_file)
                        for product in data:
                            if product['title'] == selected_product['title']:
                                if product['price'] != 'Error getting price':
                                    prices.append(float(product['price'].replace('Rs.', '').replace(',', '').strip()))
                                else:
                                    prices.append(None)  
                                scrape_dates.append(datetime.strptime(product['scrape_time'], '%Y-%m-%d %H:%M:%S'))

            if any(price is not None for price in prices):
                trace = go.Scatter(x=scrape_dates, y=prices, mode='lines+markers')

                layout = go.Layout(
                    title=f'Price Trend for "{selected_product["title"]}"',
                    xaxis=dict(title='Date'),
                    yaxis=dict(title='Price (Rs)'),
                    plot_bgcolor='#f5f5f5',  
                    paper_bgcolor='#ffffff', 
                    font=dict(color='#333333')  
                )

                fig = go.Figure(data=[trace], layout=layout)

                plot_html = fig.to_html(full_html=False)

                return render_template('price_trend_graph.html', plot_html=plot_html, product_url=selected_product['url'])
            else:
                return "No graph available for the product"
        else:
            return "Selected product not found"
    else:
        return "Invalid product source"

if __name__ == '__main__':
    app.run(debug=True)
