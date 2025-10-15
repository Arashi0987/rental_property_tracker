import requests
import xmltodict
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


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

class RealtorScrapeProvider(RentalEstimatorProvider):
    def __init__(self):
        pass

    def search_properties(self, params) -> List[Dict]:
        # Construct a Realtor.com search results page URL for rentals
        # E.g. https://www.realtor.com/realestateandhomes-search/{location}/rentals
        loc_escaped = params.loc.replace(" ", "-")
        #url = f"https://www.realtor.com/realestateandhomes-search/{loc_escaped}/type-multi-family-home,single-family-home/beds-{beds}/pnd-ctg-hide/price-{min_price}-{max_price}?view=map&pos=29.310659,-81.781098,27.785972,-80.023674,9.345502120077613&points=tc~jNifkiDkiPaf%5Dr%7DAefw%40hjXcjtAnzRsxh%40%7CmZyia%40byUaaJj%7Cb%40j%7DAdyUbfHxiEfaJyiEnuiAavf%40rad%40mwaArxiBek%60%40jdP"
        url = f'https://www.realtor.com/realestateandhomes-search/{loc_escaped}/type-multi-family-home,single-family-home/beds-{params.beds}/pnd-ctg-hide/price-{params.min_price}-{params.max_price}'
        resp = requests.get(url)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        # parse listing cards — CSS classes change, so this is fragile
        for card in soup.select(".component_property-card"):
            try:
                addr = card.select_one(".property-address").get_text(strip=True)
                price = card.select_one(".data-price").get_text(strip=True)
                # clean price string "$2,000/mo" → float
                price_val = float(price.replace("$","").replace(",","").split("/")[0])
                results.append({"address": addr, "price": price_val})
            except Exception:
                continue
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


