import os
import Actblue
import Bloomerang


import logging
import datetime
log_timestamp = datetime.datetime.timestamp(datetime.datetime.now())
this_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(this_path, '..', 'logs', str(log_timestamp) + '_delete.log')
logging.basicConfig(level=logging.DEBUG, filename=log_path, filemode='w')

ab_json = ''

import re
date_format = re.compile('\d{4}-\d{2}-\d{2}')

start_date = None  
while True:
    start_date = input("Start date? (format yyyy-mm-dd): ").strip()
    if re.fullmatch(date_format, start_date):
        break
    else:
        print("wrong format, try again")

end_date = None
while True:
    end_date = input("End date? (format yyyy-mm-dd, must be at least one day ahead of start date): ").strip()
    if re.fullmatch(date_format, end_date):
        break
    else:
        print("wrong format, try again")


from dotenv import load_dotenv
load_dotenv()

resp = Bloomerang.get('constituents?take=50&lastModified={}'.format(start_date))
logging.debug('Total Filtered: {}'.format(resp['TotalFiltered']))
constituents = resp['Results']
for constituent in constituents:
  logging.debug(constituent)

  #if this constituent was created by this program
  if constituent['AuditTrail']['CreatedName'] == os.getenv('BLOOMERANG_API_USER'):
    
    #and if it was created (not modified) in the date range
    CreatedDate = constituent['AuditTrail']['CreatedDate']
    CreatedDateObj = datetime.datetime.strptime(CreatedDate, "%Y-%m-%dT%H:%M:%SZ")
    StartDateObj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    EndDateObj = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    #note: exclude end date < not <=
    if StartDateObj <= CreatedDateObj < EndDateObj:

      logging.debug('valid delete target: {} {}'.format(constituent['FirstName'], constituent['LastName']))
      
      #first delete transactions
      transactions = Bloomerang.get('transactions?accountId={}'.format(constituent['Id']))['Results']
      logging.debug(transactions)
      for transaction in transactions:

        #double check this transaction was made by us and is in range
        if transaction['AuditTrail']['CreatedName'] == os.getenv('BLOOMERANG_API_USER'):
          TransactionCreatedDateObj = datetime.datetime.strptime(transaction['AuditTrail']['CreatedDate'], "%Y-%m-%dT%H:%M:%SZ")

          #note: exclude end date < not <=
          if StartDateObj <= TransactionCreatedDateObj < EndDateObj:

            #and delete it!
            transaction_deleted = Bloomerang.delete('transaction/{}'.format(transaction['Id']))
            logging.debug('Deleted transaction')
            logging.debug(transaction_deleted)

      #if all transactions are deleted, now delete the constituent
      constituent_deleted = Bloomerang.delete('constituent/{}'.format(constituent['Id']))
      logging.debug('deleted constituent: {} {}'.format(constituent['FirstName'], constituent['LastName']))
      logging.debug(constituent_deleted)

    else:
      logging.debug('not created in range: {} {}'.format(constituent['FirstName'], constituent['LastName']))
  
  else:
    logging.debug('not created by custom importer: {} {}'.format(constituent['FirstName'], constituent['LastName']))

import sys
sys.exit()
