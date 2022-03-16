import requests
from dotenv import load_dotenv
import os
import json

# Documentation  https://secure.actblue.com/docs/csv_api

def post(endpoint, data):

    load_dotenv()
    url = "https://secure.actblue.com/api/v1/{}".format(endpoint)
    r = requests.post(url, data=data, auth=(os.getenv('AB_UUID'), os.getenv('AB_SECRET')))
    return json.loads(r.text)
    
def get(endpoint):

    load_dotenv()
    url = "https://secure.actblue.com/api/v1/{}".format(endpoint)
    r = requests.get(url, auth=(os.getenv('AB_UUID'), os.getenv('AB_SECRET')))
    return json.loads(r.text)

def download(url, filename):
    csv = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(csv.content)
