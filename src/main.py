import os
import Actblue
import Bloomerang
try:
  import mock_data.fakey_bloomerang as mock
except:
  pass

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--auto', action='store_true')
parser.add_argument('--manual', action='store_true')
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


constituents = []
transactions = []


if args.debug:
  #we're using mock data
  constituents.append(mock.constituent())
  transactions.append(mock.transaction())
  
else:
  for ab_transaction in ab_json:
    constituent, transaction = Actblue.map_fields(ab_transaction)

    #screen for some conditions that would prevent us from importing
    #this part is CRITICAL for preventing duplicate uploads
    if not constituent['PrimaryEmail']:
      logging.debug('No email, not uploading: {} {}'.format(constituent["FirstName"], constituent['LastName']))
      continue
    if float(transaction['Amount']) < 3.0:
        if not (('PrimaryAddress' in constituent) and (constituent['PrimaryAddress']['State'] == 'NH')):
          logging.debug('Under $3 and not NH, not uploading to Bloomerang: {} {}'.format(constituent["FirstName"], constituent['LastName']))
          continue
        
    constituents.append(constituent)
    transactions.append(transaction)

if not ab_json:
  logging.debug('No transactions')
  import sys
  sys.exit()

logging.debug("ab_json")
logging.debug(ab_json)


for c, t in zip(constituents, transactions):
  constituentSearch = Bloomerang.get('constituents/search?take=6&search={} {}'.format(c['FirstName'], c['LastName']))
  
  #never seen this name before, assume new constituent
  if constituentSearch['ResultCount'] == 0:
    logging.debug('STATUS: new constituent, new transaction')
    constituentCreate = Bloomerang.post_json('constituent', c)
    logging.debug(constituentCreate)        

    t['AccountId'] = constituentCreate['Id']
    transactionCreate = Bloomerang.post_json('transaction', t)
    logging.debug(transactionCreate)
    continue
  
  #else constituent by that name already exists, verify identity
  else:
    logging.debug("c")
    logging.debug(c)
    found_const = False
    first_result = False
    for fc in constituentSearch['Results']:

      #keep log size down by only logging first (likely) match
      if not first_result:
        logging.debug("fc")
        logging.debug(fc)
        first_result = True


      #Prevent Duplicates!
      #First try to identify existing constituent by email
      #fyi we should have already filtered out c's without an email
      if (('PrimaryEmail' in fc) and ('PrimaryEmail' in c)):
        if (fc['PrimaryEmail']['Value'].lower() == c['PrimaryEmail']['Value'].lower()):
          found_const = fc
          break


      #then if no email match, try to identify by address
      #Actblue.py should have already deleted c['PrimaryAddress'] if it's blank
      if (('PrimaryAddress' in c) and ('PrimaryAddress' in fc)): 
        if (fc['PrimaryAddress']['Street'].lower() == c['PrimaryAddress']['Street'].lower() and 
            fc['PrimaryAddress']['City'].lower()   == c['PrimaryAddress']['City'].lower()):
              found_const = fc
              break


    #name matches but email and address don't, assume new constituent
    if not found_const:
      #if we don't get an email match and there's no address, it's not dupe-safe to upload
      if not ('PrimaryAddress' in c):
        logging.debug('STATUS: no email match, no address provided, skipping')
        continue

      logging.debug('STATUS: new constituent (no email/addr match), new transaction')
      constituentCreate = Bloomerang.post_json('constituent', c)
      logging.debug(constituentCreate)        

      t['AccountId'] = constituentCreate['Id']
      transactionCreate = Bloomerang.post_json('transaction', t)
      logging.debug(transactionCreate)
      continue


    #ELSE we identified this constituent in the Bloomerang search results      
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
    #don't run this on AB history before 03/04/2022 or it will duplicate transactions!
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
      logging.debug('STATUS: constituent exists, new transaction')              
      logging.debug(transactionCreate)
      continue           

  logging.debug('STATUS: constituent exists, transaction exists')
