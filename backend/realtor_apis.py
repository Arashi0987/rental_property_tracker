import time
import requests
import xmltodict
import statistics
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from homeharvest import scrape_property

class search_params():
    def __init__(self):
        self.beds = 0
        self.min_price = 0
        self.max_price = 0
        self.loc = ''

class RentalEstimatorProvider:
    def search_properties(self, location: str) -> List[Dict]:
        """Return list of property dicts (with minimum fields) or empty list on failure."""
        raise NotImplementedError

    def get_rental_estimate(self, address: str) -> Optional[float]:
        """Return rent estimate, or None on failure."""
        raise NotImplementedError

    def search_properties(self, params) -> List[Dict]:
        loc_escaped = params.loc.replace(" ", "-")
        url = f'https://www.realtor.com/realestateandhomes-search/{loc_escaped}/type-multi-family-home,single-family-home/beds-{params.beds}/pnd-ctg-hide/price-{params.min_price}-{params.max_price}'
        
        # Add headers to appear like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.realtor.com/',
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return []
        
        if resp.status_code != 200:
            print(f"Status code: {resp.status_code}")
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        
        for card in soup.select(".component_property-card"):
            try:
                addr = card.select_one(".property-address").get_text(strip=True)
                price = card.select_one(".data-price").get_text(strip=True)
                price_val = float(price.replace("$","").replace(",","").split("/")[0])
                results.append({"address": addr, "price": price_val})
            except Exception:
                continue
        
        # Add delay between requests if calling multiple times
        time.sleep(2)
        return results
    
    def get_rental_estimate(self, address: str) -> Optional[float]:
        # One approach: search rentals around the same street / zip, take average
        props = self.search_properties(address)
        rents = [p["price"] for p in props if p.get("price") is not None]
        if rents:
            # simple average
            return sum(rents) / len(rents)
        return None


class RealtorProvider(RentalEstimatorProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # This is an unofficial / third-party wrapper endpoint
        self.base_url = "https://realtor-data-api.p.rapidapi.com"  # example

    def search_properties(self, location: str) -> List[Dict]:
        url = f"{self.base_url}/properties/v2/list-for-rent"  # or “list-for-sale”
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "realtor-data-api.p.rapidapi.com"
        }
        params = {
            "location": location,
            "limit": 20
        }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json().get("properties", [])
        return []

    def get_rental_estimate(self, address: str) -> Optional[float]:
        # Realtor APIs might not provide a direct rent estimate — you may need to infer
        # from recent rental listings in that area or via a "/rent" endpoint if available
        url = f"{self.base_url}/properties/v2/detail"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "realtor-data-api.p.rapidapi.com"
        }
        params = {"address": address}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            # if they provide rent estimate field:
            rent = data.get("property", {}).get("rentalEstimate")
            if rent is not None:
                return rent
        return None


class ZillowProvider(RentalEstimatorProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.zillow.com"  # or RapidAPI wrapper URL

    def search_properties(self, location: str) -> List[Dict]:
        """Zillow is more about valuation than full listing search in public APIs; this might only return matched property info."""
        # Some Zillow endpoints let you search by address / ZIP
        # If you have a wrapper or RapidAPI endpoint:
        url = "https://zillow-api-v2.p.rapidapi.com/search"  # fictional / wrapper
        headers = {
            "X-RapidAPI-Key": self.api_key,
            # other required headers
        }
        params = {
            "location": location,
            "limit": 10,
        }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json().get("properties", [])
        return []

    def get_rental_estimate(self, address: str) -> Optional[float]:
        """Get Zillow rent estimate (Rent Zestimate) for a property"""
        # Example using the Zestimate / rent endpoint
        url = "https://www.zillow.com/webservice/GetSearchResults.htm"
        params = {
            "address": address,
            # Zillow API often requires citystatezip param
            # e.g. "citystatezip": "Seattle, WA"
            "rentzestimate": "true",
            "zws-id": self.api_key  # Zillow Web Service ID if using older API
        }
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            # Zillow’s old API returns XML, so you'd need to parse XML
            # Convert XML to dict, then extract rent estimate
            # For example using xmltodict
            
            obj = xmltodict.parse(resp.text)
            # Navigate to obj["SearchResults:searchresults"]["response"]["rentzestimate"]["amount"]["#text"]
            try:
                rent_str = obj["SearchResults:searchresults"]["response"]["rentzestimate"]["amount"]["#text"]
                return float(rent_str)
            except Exception:
                return None
        return None


#https://www.realtor.com/realestateandhomes-search/{loc}/type-multi-family-home,single-family-home/beds-{beds}/pnd-ctg-hide/price-{min_price}-{max_price}?view=map&pos=29.310659,-81.781098,27.785972,-80.023674,9.345502120077613&points=tc~jNifkiDkiPaf%5Dr%7DAefw%40hjXcjtAnzRsxh%40%7CmZyia%40byUaaJj%7Cb%40j%7DAdyUbfHxiEfaJyiEnuiAavf%40rad%40mwaArxiBek%60%40jdP
#beds int 
#min_price int
#max_price int
#loc string ("Florida", "32940", "Brevard-County_FL", or "Melbourne_FL")
#we can make a function that makes that later^

class HomeHarvestProvider(RentalEstimatorProvider):
    """
    Real estate data provider using the homeharvest library.
    Searches for properties FOR SALE and estimates rental value based on comparable rentals in the area.
    """
    
    def __init__(self):
        # homeharvest doesn't require API keys - it handles scraping internally
        pass
    
    def search_properties(self, params) -> List[Dict]:
        """
        Search for properties FOR SALE using homeharvest.
        
        Args:
            params: search_params object with beds, min_price, max_price, loc
            
        Returns:
            List of property dictionaries with address, sale price, and estimated rental value
        """
        try:
            properties = []
            
            # Scrape FOR SALE properties
            for property in scrape_property(
                location=params.loc,
                listing_type="for_sale",  
                property_type= ['single_family', 'multi_family', 'duplex_triplex']
            ):
                try:
                    # Filter by number of bedrooms
                    if params.beds > 0 and property.beds < params.beds:
                        continue
                    
                    # Get sale price
                    price = property.price
                    
                    if price is None:
                        continue
                    
                    # Filter by price range (sale price)
                    if price < params.min_price or price > params.max_price:
                        continue
                    
                    # Get estimated rental value for this property
                    rental_estimate = self._estimate_rental_value(params.loc, property.beds, property.baths)
                    
                    # Extract relevant fields
                    properties.append({
                        "address": property.address,
                        "sale_price": price,
                        "estimated_monthly_rent": rental_estimate,
                        "beds": property.beds,
                        "baths": property.baths,
                        "sqft": property.sqft,
                        "list_date": property.list_date,
                        "url": property.url
                    })
                    
                except Exception as e:
                    print(f"Error parsing property: {e}")
                    continue
            
            return properties
            
        except Exception as e:
            print(f"HomeHarvest search error: {e}")
            return []
    
    def _estimate_rental_value(self, location: str, beds: int, baths: int) -> Optional[float]:
        """
        Estimate monthly rental value by finding comparable rental properties in the area.
        
        Args:
            location: Area to search for rental comps
            beds: Number of bedrooms
            baths: Number of bathrooms
            
        Returns:
            Median monthly rent for comparable properties, or None if not found
        """
        try:
            rental_prices = []
            
            # Scrape rental properties in the same area
            for rental_prop in scrape_property(
                location=location,
                property_type="rent",
            ):
                try:
                    # Match on bedroom/bathroom count
                    if rental_prop.beds >= beds and rental_prop.baths >= baths:
                        if rental_prop.price is not None:
                            rental_prices.append(rental_prop.price)
                except Exception:
                    continue
            
            # Return median of comparable rental prices
            if rental_prices:
                return statistics.median(rental_prices)
            
            return None
            
        except Exception as e:
            print(f"Error estimating rental value: {e}")
            return None
    
    def get_rental_estimate(self, address: str) -> Optional[float]:
        """
        Get rental estimate for a specific address by finding similar rental properties nearby.
        
        Args:
            address: Property address or area
            
        Returns:
            Estimated monthly rent or None if not found
        """
        try:
            # Search for rentals in that area and get the median
            rental_prices = []
            
            for property in scrape_property(
                location=address,
                property_type="rent",
            ):
                if property.price is not None:
                    rental_prices.append(property.price)
            
            if rental_prices:
                return statistics.median(rental_prices)
            
            return None
            
        except Exception as e:
            print(f"HomeHarvest rental estimate error: {e}")
            return None


# Updated usage example
def main():
    print('Testing HomeHarvest Provider - Finding Investment Properties')
    params = search_params()
    params.beds = 3
    params.min_price = 150000  # Looking for homes priced $200k-$400k
    params.max_price = 400000
    params.loc = "Florida"
    
    provider = HomeHarvestProvider()
    results = provider.search_properties(params)
    
    print(f"\nFound {len(results)} properties for sale:")
    print("-" * 80)
    
    for prop in results:
        if prop['estimated_monthly_rent']:
            annual_rent = prop['estimated_monthly_rent'] * 12
            roi = (annual_rent / prop['sale_price']) * 100
            print(f"Address: {prop['address']}")
            print(f"  Sale Price: ${prop['sale_price']:,}")
            print(f"  Est. Monthly Rent: ${prop['estimated_monthly_rent']:.0f}")
            print(f"  Est. Annual Rent: ${annual_rent:,.0f}")
            print(f"  Gross ROI: {roi:.2f}%")
            print()
    
    # Save to file
    with open("test.txt", "w") as text_file:
        text_file.write(str(results))


if __name__ == "__main__":
    main()