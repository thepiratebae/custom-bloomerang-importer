import Actblue
import Bloomerang
import mock_data.fakey_bloomerang as mock

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--auto', action='store_true')
parser.add_argument('--manual', action='store_true')
args = parser.parse_args()

import logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w')

ab_json = ''

if args.auto:
  import datetime
  today = datetime.date.today().strftime("%Y-%m-%d")
  tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
  ab_json = Actblue.get_contributions(today, tomorrow)

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


constituents = []
transactions = []

if args.debug:
  #we're using mock data
  constituents.append(mock.constituent())
  transactions.append(mock.transaction())
  
else:
  for ab_transaction in ab_json:
    constituent, transaction = Actblue.map_fields(ab_transaction)
    constituents.append(constituent)
    transactions.append(transaction)

if not ab_json:
  logging.debug('No transactions')
  import sys
  sys.exit()

logging.debug("ab_json")
logging.debug(ab_json)

input('Press enter to upload to bloomerang...')

for c, t in zip(constituents, transactions):
  constituentSearch = Bloomerang.get('constituents/search?search={} {}'.format(c['FirstName'], c['LastName']))
  
  #never seen this name before, assume new constituent
  if constituentSearch['ResultCount'] == 0:
    logging.debug('new constituent, new transaction')
    constituentCreate = Bloomerang.post_json('constituent', c)
    logging.debug(constituentCreate)        

    t['AccountId'] = constituentCreate['Id']
    transactionCreate = Bloomerang.post_json('transaction', t)
    logging.debug(transactionCreate)
    continue
  
  #constituent by that name already exists, use address to verify identity
  else:
    found_const = False
    for fc in constituentSearch['Results']:
      logging.debug("fc")
      logging.debug(fc)
      logging.debug("c")
      logging.debug(c)
      if (fc['PrimaryAddress']['Street'].lower() == c['PrimaryAddress']['Street'].lower() and 
          fc['PrimaryAddress']['City'].lower()   == c['PrimaryAddress']['City'].lower() and
          fc['PrimaryAddress']['Type'].lower()   == c['PrimaryAddress']['Type'].lower()):
            found_const = fc
            break

    #name matches but address doesn't, assume new constituent
    if not found_const:
      logging.debug('new constituent (same name), new transaction')
      constituentCreate = Bloomerang.post_json('constituent', c)
      logging.debug(constituentCreate)        

      t['AccountId'] = constituentCreate['Id']
      transactionCreate = Bloomerang.post_json('transaction', t)
      logging.debug(transactionCreate)
      continue

          
    #constituent exists, verify transaction doesn't already exist
    query_str = 'accountId={}&minAmount={}&maxAmount={}'.format(found_const['Id'], t['Amount'], t['Amount'])
    found_trans = Bloomerang.get('transactions?{}'.format(query_str))

    #get all transactions made on this day
    datematches = []
    for ft in found_trans['Results']:
      if ft['Date'] == t['Date'][:10]: #this date slice may only work for actblue imports!
        datematches.append(ft)
    
    #check that the one we're importing doesn't already exist
    #by using the unique Actblue ReceiptId we stored in a custom field 
    #don't run this on AB history before _____ or it will duplicate transactions!
    id_already_exists = False
    for dm in datematches:
      for value in dm['Designations'][0]['CustomValues']:
        if value['FieldId'] == 854016: #field: external payment id
          t['Designations'][0]['CustomValues'][0]['Value']
          if value['Value']['Value'] == t['Designations'][0]['CustomValues'][0]['Value']:
            id_already_exists = True
    
    if not id_already_exists:
      t['AccountId'] = found_const['Id']
      transactionCreate = Bloomerang.post_json('transaction', t)
      logging.debug('constituent exists, new transaction')              
      logging.debug(transactionCreate)
      continue           

  logging.debug('constituent exists, transaction exists')
