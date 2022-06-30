import os
import Actblue
import Bloomerang
import GoogleSheets
try:
  import mock_data.fakey_bloomerang as mock
except:
  pass

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--auto', action='store_true')
parser.add_argument('--manual', action='store_true')
parser.add_argument('--sheets', action='store_true')
args = parser.parse_args()


import logging
import datetime
log_timestamp = datetime.datetime.timestamp(datetime.datetime.now())
this_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(this_path, '..', 'logs', str(log_timestamp) + '.log')
# logging.basicConfig(level=logging.DEBUG, filename='logs/{}.log'.format(log_timestamp), filemode='w')
logging.basicConfig(level=logging.DEBUG, filename=log_path, filemode='w')

ab_json = ''

#this is how the program is set up to run automatically on a server, every day
if args.auto:
  today = datetime.date.today().strftime("%Y-%m-%d")
  yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
  tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
  ab_json = Actblue.get_contributions(yesterday, tomorrow)
  logging.debug('Range: {} to {}'.format(yesterday, tomorrow))


#this is how it's set up to run on an arbitrary date range 
elif args.manual:
  import re
  date_format = re.compile('\d{4}-\d{2}-\d{2}')
  
  while True:
    start_date = input("Start date? (format yyyy-mm-dd): ").strip()
    if re.fullmatch(date_format, start_date):
      break
    else:
      print("wrong format, try again")

  while True:
    end_date = input("End date? (format yyyy-mm-dd, must be at least one day ahead of start date): ").strip()
    if re.fullmatch(date_format, end_date):
      break
    else:
      print("wrong format, try again")

  ab_json = Actblue.get_contributions(start_date, end_date)
  logging.debug('Range: {} to {}'.format(start_date, end_date))
  logging.debug(ab_json)


#collecting everything for Bloomerang CRM here
#but Bloomerang charges per constituent
constituents = []
transactions = []

#so lower value targets that we get nationwide from NNAF go here
#to be added to a Google Spreadsheet
sheets_constituents = []
sheets_transactions = []


if args.debug:
  #we're using mock data
  constituents.append(mock.constituent())
  transactions.append(mock.transaction())
  
else:
  for ab_transaction in ab_json:
    constituent, transaction = Actblue.map_fields(ab_transaction)

    #screen for some conditions that would prevent us from importing
    #this part is CRITICAL for preventing duplicate uploads
    #and handling junk data from the NNAF form

    #if not NH
    if not (('PrimaryAddress' in constituent) and 
            ('State' in constituent['PrimaryAddress']) and
            (constituent['PrimaryAddress']['State'] == 'NH')):
  
      #if below giving threshold
      if float(transaction['Amount']) < 3.0:
        logging.debug('Under $3 and not NH, skip: {} {}'.format(constituent["FirstName"], constituent['LastName']))
        sheets_constituents.append(constituent)
        sheets_transactions.append(transaction)
        continue
  
      #if no email
      if not ('PrimaryEmail' in constituent):
        logging.debug('No email, not NH, skip: {} {}'.format(constituent["FirstName"], constituent['LastName']))
        sheets_constituents.append(constituent)
        sheets_transactions.append(transaction)
        continue

    #must have either address or email
    if not (('PrimaryAddress' in constituent) or ('PrimaryEmail' in constituent)):
        logging.debug('No email or address, skip: {} {}'.format(constituent["FirstName"], constituent['LastName']))
        continue      

        
    constituents.append(constituent)
    transactions.append(transaction)

if not ab_json:
  logging.debug('No transactions')
  import sys
  sys.exit()

logging.debug("ab_json")
logging.debug(ab_json)


for c, t in zip(sheets_constituents, sheets_transactions):
  GoogleSheets.Upload(c, t)

if args.sheets:
  sys.exit()

for c, t in zip(constituents, transactions):
  Bloomerang.Upload(c, t)
