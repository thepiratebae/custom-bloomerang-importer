
# import httplib2
import os
from dotenv import load_dotenv

from apiclient import discovery
from google.oauth2 import service_account

import logging

#ranges key
tx_id = 'D2:D'
table_append = 'A1:O'
table_sort = "database!A1:O"


def GenerateRow(constituent, transaction):
  c = constituent
  t = transaction
  
  #prevent key errors on missing fields
  if not 'PrimaryEmail' in c:
    c['PrimaryEmail'] = {'Value': ''}
  if not 'PrimaryPhone' in c:
    c['PrimaryPhone'] = {'Number': ''}
  if not 'PrimaryAddress' in c:
    c['PrimaryAddress'] = {'Street': '', 'City': '', 'State': '', 'PostalCode': '', 'Country': ''}
  if not 'Street' in c['PrimaryAddress']:
    c['PrimaryAddress']['Street'] = ''
  if not 'City' in c['PrimaryAddress']:
    c['PrimaryAddress']['City'] = ''
  if not 'State' in c['PrimaryAddress']:
    c['PrimaryAddress']['State'] = ''
  if not 'Country' in c['PrimaryAddress']:
    c['PrimaryAddress']['Country'] = ''
  if not 'PostalCode' in c['PrimaryAddress']:
    c['PrimaryAddress']['PostalCode'] = ''

  return  [
            t['Date'], t['Amount'], t['Designations'][0]['Note'], t['Designations'][0]['CustomValues'][0]['Value'],
            c['FirstName'], c['LastName'], c['JobTitle'], c['Employer'], c['PrimaryEmail']['Value'], c['PrimaryPhone']['Number'],
            c['PrimaryAddress']['Street'], c['PrimaryAddress']['City'], c['PrimaryAddress']['State'], c['PrimaryAddress']['PostalCode'], c['PrimaryAddress']['Country'] 
          ]


def Upload(rows):
  #connect to spreadsheet
  scopes = ["https://www.googleapis.com/auth/spreadsheets"]
  this_path = os.path.dirname(os.path.abspath(__file__))
  secret_file = os.path.join(this_path, '..', 'client_secret.json')
  # secret_file = os.path.join(os.getcwd(), 'client_secret.json')
  load_dotenv()
  spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
  credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
  service = discovery.build('sheets', 'v4', credentials=credentials)


  #retrieve and flatten all existing transaction ids
  result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=tx_id).execute()
  transactionIDs = []
  try:
    for id in result['values']:
      transactionIDs.append(id[0])
  except KeyError:
    pass

  #delete row if we've already recorded that transaction
  unique_rows = []
  for row in rows:
    if not row[3] in transactionIDs:
      unique_rows.append(row)

  body = {
      'values': unique_rows
  }
  result = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=table_append, body=body, valueInputOption='USER_ENTERED').execute()


def Sort():
  # from googleapiclient import discovery
  #connect to spreadsheet
  scopes = ["https://www.googleapis.com/auth/spreadsheets"]
  this_path = os.path.dirname(os.path.abspath(__file__))
  secret_file = os.path.join(this_path, '..', 'client_secret.json')
  # secret_file = os.path.join(os.getcwd(), 'client_secret.json')
  load_dotenv()
  spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
  credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
  service = discovery.build('sheets', 'v4', credentials=credentials)


  requests = []
  requests.append({
    "sortRange": {
      "range": { 
        "sheetId": 0,
        "startRowIndex": 0,
        # "endRowIndex": integer,
        "startColumnIndex": 0,
        "endColumnIndex": 14
      },
      "sortSpecs": [
        {
          "sortOrder": "DESCENDING",
          "dimensionIndex": 0
        }
      ]
    }
  })

  body = {
      'requests': requests
  }

  request = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body)
  response = request.execute()

  # from pprint import pprint
  # pprint(response)