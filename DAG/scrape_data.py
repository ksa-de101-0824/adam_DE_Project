import requests
from bs4 import BeautifulSoup
import pandas as pd

url = 'https://data.gov.my/data-catalogue/ridership_headline'

def scrape_data():
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract relevant data (you'll need to inspect the page structure)
    # Example: Parse ridership data by transport mode, station, year, and month
    data = []

    # Loop over HTML elements and extract data, then append to `data`
    for row in soup.find_all('tr'):  # Modify based on the real HTML structure
        cells = row.find_all('td')
        if cells:
            mode = cells[0].text.strip()  # transport mode
            station = cells[1].text.strip()  # station (if available)
            year = cells[2].text.strip()  # year
            month = cells[3].text.strip()  # month
            ridership = cells[4].text.strip()  # ridership count
            
            data.append([mode, station, year, month, ridership]) 

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(data, columns=['Mode', 'Station', 'Year', 'Month', 'Ridership'])
    return df

if __name__ == "__main__":
    df = scrape_data()
    print(df.head())
