import os
import requests

url="https://api.twelvedata.com"
api="6a7c4a11380c48c0a644dd1cd06f2702"

def fetch_current_price(symbol:str):
    endpoint=f"{url}/price"

    params={ "symbol":symbol.upper(),"apikey":api}

    res=requests.get(endpoint,params=params)

    data=res.json()

    if "price" in data:
        return{
            "symbol":symbol.upper(),
            "price":float(data["price"]),
        }
    else:
        raise Exception(f"Error fetching price for {symbol}: {data.get('message', 'Unknown error')}")
    

    







    