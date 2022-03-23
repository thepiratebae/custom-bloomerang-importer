import requests
from dotenv import load_dotenv
import os
import json

# Documentation  https://bloomerang.co/product/integrations-data-management/api/rest-api/

domain = 'https://api.bloomerang.co/v2/'

def get(endpoint):

    load_dotenv()
    url = "{}{}".format(domain, endpoint)
    header = {
        "X-API-KEY": os.getenv('BLOOMERANG_KEY')
    }
    r = requests.get(url, headers=header)
    return json.loads(r.text)
    

