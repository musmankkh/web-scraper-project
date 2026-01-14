from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time

url = "https://www.fresha.com/lp/en/ae-dubai"

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in background
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

try:
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    
    print("Website loaded!")
    
    # Wait for the page to load
    time.sleep(3)
    
    # Get the page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    main_div = soup.find('div', class_='ts_bNq')
    venues = []

    if main_div:
        print("\n✓ Found main div (ts_bNq)")
        target_divs = main_div.find_all('div', class_='paUULP Z1aKNU')
        print(f"✓ Found {len(target_divs)} venues")

        for idx, target_div in enumerate(target_divs, 1):
            print(f"\n--- Processing Venue {idx} ---")
            
            # Find the venue link
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
                name_p = nd2h5g_div.find('p', class_='axDOAG zL1l9a deeUT2')
                if name_p:
                    name = name_p.get_text(strip=True).encode('utf-8', errors='ignore').decode('utf-8')
                print(f"Name: {name}")

                address_p = nd2h5g_div.find('p', class_='axDOAG TE8kwS DbgFmO deeUT2')
                if address_p:
                    address = address_p.get_text(strip=True).encode('utf-8', errors='ignore').decode('utf-8')
                print(f"Address: {address}")

                rate_p = nd2h5g_div.find("p", class_="axDOAG VH00E7 qLhAks SycVRT")
                if rate_p:
                    rating = rate_p.get_text(strip=True)
                print(f"Rating: {rating}")

            # Extract gender
            badge_div = a_tag.find('div', class_='aAeYXF')
            gender_type = "N/A"
            if badge_div:
                badges = badge_div.find_all('span', class_='axDOAG K8UigX qLhAks cy3ZMU fhrg9J X4Krsb')
                for badge in badges:
                    badge_text = badge.get_text(strip=True)
                    if badge_text in ["Men only", "Women only"]:
                        gender_type = badge_text
                        break
            print(f"Gender: {gender_type}")

            # Extract services
            services = []
            prices = []
            services_container = a_tag.find('div', class_='rI9TZu')
            if services_container:
                service_items = services_container.find_all('div', class_='Tu5F90')
                for service_item in service_items:
                    service_name_p = service_item.find('p', class_='axDOAG TE8kwS qLhAks deeUT2')
                    if service_name_p:
                        service_name = service_name_p.get_text(strip=True).encode('utf-8', errors='ignore').decode('utf-8')
                    else:
                        service_name = "N/A"

                    price_p = service_item.find('p', class_='axDOAG VH00E7 qLhAks Llk4pS Pv0mOj')
                    if price_p:
                        price = price_p.get_text(strip=True).replace('\xa0', ' ').encode('utf-8', errors='ignore').decode('utf-8')
                    else:
                        price = "N/A"

                    services.append(service_name)
                    prices.append(price)

            # Now visit the venue page to get opening times
            opening_times = {
                'Monday': 'N/A',
                'Tuesday': 'N/A',
                'Wednesday': 'N/A',
                'Thursday': 'N/A',
                'Friday': 'N/A',
                'Saturday': 'N/A',
                'Sunday': 'N/A'
            }

            if venue_url:
                try:
                    print(f"Visiting venue page: {venue_url}")
                    driver.get(venue_url)
                    time.sleep(3)
                    
                    # Parse the venue page
                    venue_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # Find opening hours section
                    opening_hours_rows = venue_soup.find_all('div', {'data-qa': 'opening-hours-row'})
                    
                    for row in opening_hours_rows:
                        day_p = row.find('p', {'data-qa': 'opening-hours-day'})
                        hours_p = row.find('p', {'data-qa': 'opening-hours-range'})
                        
                        if day_p and hours_p:
                            day = day_p.get_text(strip=True)
                            hours = hours_p.get_text(strip=True)
                            opening_times[day] = hours
                    
                    print(f"Opening times extracted: {opening_times}")
                    
                except Exception as e:
                    print(f"Error getting opening times: {e}")

            # Store venue data
            venue_data = {
                'name': name,
                'address': address,
                'gender': gender_type,
                'rating': rating,
                'services_list': services,
                'prices_list': prices,
                'Monday': opening_times['Monday'],
                'Tuesday': opening_times['Tuesday'],
                'Wednesday': opening_times['Wednesday'],
                'Thursday': opening_times['Thursday'],
                'Friday': opening_times['Friday'],
                'Saturday': opening_times['Saturday'],
                'Sunday': opening_times['Sunday']
            }
            venues.append(venue_data)

        # Save to Excel
        if venues:
            max_services = max(len(v['services_list']) for v in venues) if venues else 0

            # Prepare data for DataFrame with side-by-side format
            excel_data = []
            
            for v in venues:
                row = {
                    'Name': v['name'],
                    'Address': v['address'],
                    'Gender': v['gender'],
                    'Rating': v['rating'],
                    'Monday': v['Monday'],
                    'Tuesday': v['Tuesday'],
                    'Wednesday': v['Wednesday'],
                    'Thursday': v['Thursday'],
                    'Friday': v['Friday'],
                    'Saturday': v['Saturday'],
                    'Sunday': v['Sunday']
                }

                # Add service and price columns SIDE BY SIDE
                for i in range(max_services):
                    svc_val = v['services_list'][i] if i < len(v['services_list']) else "N/A"
                    prc_val = v['prices_list'][i] if i < len(v['prices_list']) else "N/A"
                    
                    # This creates: Service_1, Price_1, Service_2, Price_2, etc.
                    row[f"Service_{i+1}"] = svc_val
                    row[f"Price_{i+1}"] = prc_val

                excel_data.append(row)

            # Create DataFrame with ordered columns
            # First the basic info, then alternating service/price pairs
            base_columns = ['Name', 'Address', 'Gender', 'Rating', 
                          'Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                          'Friday', 'Saturday', 'Sunday']
            
            service_price_columns = []
            for i in range(max_services):
                service_price_columns.append(f"Service_{i+1}")
                service_price_columns.append(f"Price_{i+1}")
            
            column_order = base_columns + service_price_columns
            
            df = pd.DataFrame(excel_data)
            df = df[column_order]  # Reorder columns
            
            # Save to Excel with formatting
            excel_filename = 'datas.xlsx'
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Venues', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Venues']
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    ) + 2
                    # Convert column index to Excel column letter
                    col_letter = ''
                    temp_idx = idx
                    while temp_idx >= 0:
                        col_letter = chr(65 + (temp_idx % 26)) + col_letter
                        temp_idx = temp_idx // 26 - 1
                    worksheet.column_dimensions[col_letter].width = min(max_length, 50)

            print(f"\n✓ Extracted {len(venues)} venues with opening times")
            print(f"✓ Data saved to '{excel_filename}'")
            print(f"✓ Format: Service_1 | Price_1 | Service_2 | Price_2 | ...")
    
    driver.quit()

except Exception as e:
    print(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()