import requests
from woocommerce import API

# WooCommerce API credentials
store_url = "https://naomidror.com/"
consumer_key = "ck_14a2ef6580c67a35d294afa5ddc81d628065beb0"
consumer_secret = "cs_7eed1906318dd618bd860d078bc219d5420e992f"

wcapi = API(url=store_url,consumer_key=consumer_key,consumer_secret=consumer_secret,version="wc/v3")

if wcapi:
    print("Connected to WooCommerce API")
    print(wcapi.get("orders/54510").json())

else:
    print("Failed to connect to WooCommerce API")
