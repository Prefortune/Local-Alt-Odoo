import csv
import requests

# Replace 'demo' with your actual API key
API_KEY = 'RH74P313JDDPBLHY'
CSV_URL = f'https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey={API_KEY}'

# Make a request to the Alpha Vantage IPO Calendar API
with requests.Session() as s:
    response = s.get(CSV_URL)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Decode and parse the CSV content
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        ipo_data = list(cr)
        
        # Print the IPO data
        for row in ipo_data:
            print(row)
    else:
        print(f"Error fetching data. Status code: {response.status_code}")
