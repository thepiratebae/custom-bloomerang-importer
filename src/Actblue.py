from tracemalloc import start
import requests
from dotenv import load_dotenv
import os
import json
import csv

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


def download_csv_to_json(url):
    csv_download = requests.get(url)

    csv_lines = csv_download.content.decode("utf-8").splitlines()

    jsonArray = []
    csvReader = csv.DictReader(csv_lines, delimiter=',') 
    for row in csvReader: 
        jsonArray.append(row)

    return json.dumps(jsonArray, indent=4)
 

def get_contributions(start_date, end_date):
    data = {
        "csv_type": "paid_contributions",
        "date_range_start": start_date,
        "date_range_end": end_date,
    }
    id = post('csvs', data)['id']

    resp = get('csvs/{}'.format(id))
    while resp['status'] != 'complete':
        time.sleep(5)
        resp = get('csvs/{}'.format(id))

    return download_csv_to_json(resp['download_url'])
