from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # For EC2, you might need to specify chromedriver path
    # service = Service('/usr/local/bin/chromedriver')
    # driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_fresha_venues(url, output_dir='output'):
    """Main scraping function"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        print(f"✓ Website loaded: {url}")
        
        # Wait for page to load
        time.sleep(3)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        main_div = soup.find('div', class_='ts_bNq')
        
        venues = []
        
        if main_div:
            print("✓ Found main div (ts_bNq)")
            target_divs = main_div.find_all('div', class_='paUULP Z1aKNU')
            print(f"✓ Found {len(target_divs)} venues")
            
            for idx, target_div in enumerate(target_divs, 1):
                print(f"\n--- Processing Venue {idx}/{len(target_divs)} ---")
                
                # Find venue link
                a_tag = target_div.find('a', class_='OP1nBW KzVzOx')
                if not a_tag:
                    continue
                
                # Get venue URL
                venue_url = a_tag.get('href')
                if venue_url and not venue_url.startswith('http'):
                    venue_url = 'https://www.fresha.com' + venue_url
                
                # Extract basic info
                nd2h5g_div = a_tag.find('div', class_='nd2h5g')
                name = address = rating = "N/A"
                
                if nd2h5g_div:
                    name_p = nd2h5g_div.find('p', class_='axDOAG zL1l9a deeUT2 NH5kAF')
                    if name_p:
                        name = name_p.get_text(strip=True).encode('utf-8', errors='ignore').decode('utf-8')
                        print(f"Name: {name}")
                    
                    address_p = nd2h5g_div.find('p', class_='axDOAG TE8kwS DbgFmO deeUT2')
                    if address_p:
                        address = address_p.get_text(strip=True).encode('utf-8', errors='ignore').decode('utf-8')
                        print(f"Address: {address}")
                    
                    rate_p = nd2h5g_div.find("p", class_="axDOAG VH00E7 eGBYyp SycVRT tWrves")
                    if rate_p:
                        rating = rate_p.get_text(strip=True)
                        print(f"Rating: {rating}")
  
                
                # Get opening times
                opening_times = {
                    'Monday': 'N/A', 'Tuesday': 'N/A', 'Wednesday': 'N/A',
                    'Thursday': 'N/A', 'Friday': 'N/A', 'Saturday': 'N/A', 'Sunday': 'N/A'
                }
                
                if venue_url:
                    try:
                        print(f"Visiting venue page: {venue_url}")
                        driver.get(venue_url)
                        time.sleep(3)
                        
                        venue_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        opening_hours_rows = venue_soup.find_all('div', {'data-qa': 'opening-hours-row'})
                        
                        for row in opening_hours_rows:
                            day_p = row.find('p', {'data-qa': 'opening-hours-day'})
                            hours_p = row.find('p', {'data-qa': 'opening-hours-range'})
                            if day_p and hours_p:
                                day = day_p.get_text(strip=True)
                                hours = hours_p.get_text(strip=True)
                                opening_times[day] = hours
                        
                        print(f"Opening times: {opening_times}")
                    except Exception as e:
                        print(f"Error getting opening times: {e}")
                
                # Store venue data
                venue_data = {
                    'name': name,
                    'address': address,
                    'rating': rating,
                  
                    **opening_times
                }
                venues.append(venue_data)
        
        # Save to Excel
        if venues:
            save_to_excel(venues, output_dir)
            print(f"\n✓ Successfully extracted {len(venues)} venues")
            return True
        else:
            print("\n✗ No venues found")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def save_to_excel(venues, output_dir):
    """Save venues data to Excel file"""
 
    excel_data = []
    for v in venues:
        row = {
            'Name': v['name'],
            'Address': v['address'],
            'Rating': v['rating'],
            'Monday': v['Monday'],
            'Tuesday': v['Tuesday'],
            'Wednesday': v['Wednesday'],
            'Thursday': v['Thursday'],
            'Friday': v['Friday'],
            'Saturday': v['Saturday'],
            'Sunday': v['Sunday']
        }
        
        # Add service and price columns side by side
    
        
        excel_data.append(row)
    
    df = pd.DataFrame(excel_data)
    
    # Reorder columns
    base_cols = ['Name', 'Address', 'Rating', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
 
    
    df = df[base_cols]     
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = os.path.join(output_dir, f'fresha_venues_{timestamp}.xlsx')
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Venues', index=False)
        
        worksheet = writer.sheets['Venues']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
            worksheet.column_dimensions[col_letter].width = min(max_length, 50)
    
    print(f"✓ Data saved to: {excel_filename}")
    return excel_filename

if __name__ == "__main__":
    url = "https://www.fresha.com/lp/en/ae-dubai"
    scrape_fresha_venues(url)