from tracemalloc import start
import requests
from dotenv import load_dotenv
import os
import json
import csv
import time 

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

    return json.loads(json.dumps(jsonArray, indent=4))
 

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


# map actblue fields to bloomerang fields
def map_fields(ab_transaction):
    constituent = {
        "Type": "Individual",
        "Status": "Active",
        "FirstName": ab_transaction['Donor First Name'],
        "LastName": ab_transaction['Donor Last Name'],
        "JobTitle": ab_transaction['Donor Occupation'],
        "Employer": ab_transaction['Donor Employer'],
        "PrimaryEmail": {
        "Type": "Home",
        "Value": ab_transaction['Donor Email'],
        },
        "PrimaryPhone": {
        "Type": "Home",
        "Number": ab_transaction['Donor Phone'],
        },
        "PrimaryAddress": {
        "Type": "Home",
        "Street": "{} {}".format(ab_transaction['Donor Addr1'], ab_transaction['Donor Addr2']),
        "City": ab_transaction['Donor City'],
        "State": ab_transaction['Donor State'],
        "PostalCode": ab_transaction['Donor ZIP'],
        "Country": ab_transaction['Donor Country'],
        },
    }


    # bloomerang errors on uploading these fields with partial values
    if constituent['PrimaryPhone']['Number'] == '':
        del constituent['PrimaryPhone']

    # bloomerang errors on uploading these fields with partial values
    if constituent['PrimaryEmail']['Value'] == '':
        del constituent['PrimaryEmail']

    #some uploads don't provide an address, somehow. Bloomerang wont let us upload with partial address so delete it
    if constituent['PrimaryAddress']['City'] == '':
        del constituent['PrimaryAddress']

    elif constituent['PrimaryAddress']['Country'] == '':
        del constituent['PrimaryAddress'] 
    
    # 'City, State, and PostalCode are not allowed to be used for international addresses. 
    # Include city, state, and postal code in Street field instead.'
    elif constituent['PrimaryAddress']['Country'] != 'United States':
        constituent['PrimaryAddress']['Street'] += '{}, {} {}'.format(constituent['PrimaryAddress']['City'], 
                                                                    constituent['PrimaryAddress']['State'],
                                                                    constituent['PrimaryAddress']['PostalCode'])
        del constituent['PrimaryAddress']['City']
        del constituent['PrimaryAddress']['State']
        del constituent['PrimaryAddress']['PostalCode']


    transaction = {
        'Date': ab_transaction['Date'],
        'Amount': ab_transaction['Amount'],
        'Method': 'CreditCard',
        # 'AccountId': Must get this from new constituent, otherwise search constituent
        "Designations": [
        {
            "Amount": ab_transaction['Amount'],
            "Note": ab_transaction["Reference Code"],
            "Type": "Donation",
            # "FundId": 840704, #fund: api_test
            "FundId": 10, #fund: Unrestricted
            "CustomValues": [
            {
                "FieldId": 854016, #external payment id custom field
                "Value": ab_transaction['Receipt ID'] #actblue receipt id, for example
            }
        ]
        },        
        ]
    }
    
    return constituent, transaction