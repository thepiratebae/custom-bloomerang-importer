
# import httplib2
import os
from dotenv import load_dotenv

from apiclient import discovery
from google.oauth2 import service_account

import logging

import time


def Upload(constituent, transaction):
  c = constituent
  t = transaction

  #connect to spreadsheet
  scopes = ["https://www.googleapis.com/auth/spreadsheets"]
  secret_file = os.path.join(os.getcwd(), 'client_secret.json')
  load_dotenv()
  spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
  credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
  service = discovery.build('sheets', 'v4', credentials=credentials)
  
  #ranges key
  tx_id = 'D2:D'
  table_append = 'A1:O'

  #search if transaction id already exists
  result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=tx_id).execute()
  transactionIDs = []
  for id in result['values']:
    transactionIDs.append(id[0])

  print(result)
  print(t['Designations'][0]['CustomValues'][0]['Value'])
  print(transactionIDs) 
  if t['Designations'][0]['CustomValues'][0]['Value'] in transactionIDs:
    #bail if we've already recorded this transaction
    return

  #flatten the constituent and transaction objects 

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


  values = [
      [
          t['Date'], t['Amount'], t['Designations'][0]['Note'], t['Designations'][0]['CustomValues'][0]['Value'],
              c['FirstName'], c['LastName'], c['JobTitle'], c['Employer'], c['PrimaryEmail']['Value'], c['PrimaryPhone']['Number'],
              c['PrimaryAddress']['Street'], c['PrimaryAddress']['City'], c['PrimaryAddress']['State'], c['PrimaryAddress']['PostalCode'], c['PrimaryAddress']['Country'] 
      ],
      # Additional rows ...
  ]

  body = {
      'values': values
  }
  result = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=table_append, body=body, valueInputOption='USER_ENTERED').execute()

  time.sleep(1.1)