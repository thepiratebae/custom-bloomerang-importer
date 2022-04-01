import Actblue
import Bloomerang
import logging
import mock_data.fakey_bloomerang as mock

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w')

from datetime import date
today = date.today().strftime("%Y-%m-%d")

# keep commented out to use mock data
# ab_json = Actblue.get_contributions('2022-01-01', today)

constituents = []
transactions = []

try:
  for ab_transaction in ab_json:
      constituent, transaction = Actblue.map_fields(ab_transaction)
      constituents.append(constituent)
      transactions.append(transaction)

except:
  pass

constituents.append(mock.constituent())
transactions.append(mock.transaction())


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
