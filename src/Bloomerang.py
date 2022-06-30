import requests
from dotenv import load_dotenv
import os
import json
import logging

# Documentation  https://bloomerang.co/product/integrations-data-management/api/rest-api/

domain = 'https://api.bloomerang.co/v2/'

def get(endpoint):

    load_dotenv()
    url = "{}{}".format(domain, endpoint)
    header = {
        "X-API-KEY": os.getenv('BLOOMERANG_KEY')
    }
    r = requests.get(url, headers=header)
    return json.loads(r.text)
    

def post(endpoint, _data):
    load_dotenv()
    url = "{}{}".format(domain, endpoint)
    header = {
        "X-API-KEY": os.getenv('BLOOMERANG_KEY')
    }
    r = requests.post(url, data=_data, headers=header)
    return json.loads(r.text)


def delete(endpoint):
    load_dotenv()
    url = "{}{}".format(domain, endpoint)
    header = {
        "X-API-KEY": os.getenv('BLOOMERANG_KEY')
    }
    r = requests.delete(url, headers=header)
    return json.loads(r.text)


# def deleteTransactionsOnConstituent(id):
#     transactions = get('transactions?accountId'.format(id))


def post_json(endpoint, _json):
    load_dotenv()
    url = "{}{}".format(domain, endpoint)
    header = {
        "X-API-KEY": os.getenv('BLOOMERANG_KEY')
    }
    r = requests.post(url, json=_json, headers=header)
    return json.loads(r.text)


def Upload(constituent, transaction):
  c = constituent
  t = transaction

  constituentSearch = get('constituents/search?take=6&search={} {}'.format(c['FirstName'], c['LastName']))
  
  #never seen this name before, assume new constituent
  if constituentSearch['ResultCount'] == 0:
    logging.debug('STATUS: new constituent, new transaction')
    constituentCreate = post_json('constituent', c)
    logging.debug(constituentCreate)        

    t['AccountId'] = constituentCreate['Id']
    transactionCreate = post_json('transaction', t)
    logging.debug(transactionCreate)
    # continue
    return 
  
  #else constituent by that name already exists, verify identity
  else:
    logging.debug("c")
    logging.debug(c)

    found_const = False
    for fc in constituentSearch['Results']:


      #Prevent Duplicates!
      #First try to identify existing constituent by email
      #fyi we should have already filtered out c's without an email
      if (('PrimaryEmail' in fc) and ('PrimaryEmail' in c)):
        if (fc['PrimaryEmail']['Value'].lower() == c['PrimaryEmail']['Value'].lower()):
          found_const = fc
          logging.debug("fc")
          logging.debug(fc)
          break

        
      #then if no email match, try to match by name, street, city
      #Actblue.py should have already deleted c['PrimaryAddress'] if it's blank
      try:
        if (c['FirstName'].lower().strip() == fc['FirstName'].lower().strip() and c['LastName'].lower().strip() == fc['LastName'].lower().strip()):
          if (('PrimaryAddress' in c) and ('PrimaryAddress' in fc)): 
            if (fc['PrimaryAddress']['Street'].lower().strip() == c['PrimaryAddress']['Street'].lower().strip() and 
                fc['PrimaryAddress']['City'].lower().strip()   == c['PrimaryAddress']['City'].lower().strip()):
                  found_const = fc
                  logging.debug("fc")
                  logging.debug(fc)
                  break
      except:
        #sometimes it tries to compare to an address without street, 
        #i think these were imported manually before this program existed
        pass


    #no match in the search results, assume new constituent
    if not found_const:

      #if we don't get an email match and there's no address, it's not dupe-safe to upload
      if not ('PrimaryAddress' in c):
        logging.debug('STATUS: no email match, no address provided, skipping')
        return

      logging.debug('STATUS: new constituent (no email/addr match), new transaction')
      constituentCreate = post_json('constituent', c)
      logging.debug(constituentCreate)        

      t['AccountId'] = constituentCreate['Id']
      transactionCreate = post_json('transaction', t)
      logging.debug(transactionCreate)
      return


    #ELSE we identified this constituent in the Bloomerang search results      
    #constituent exists, verify transaction doesn't already exist
    query_str = 'accountId={}&minAmount={}&maxAmount={}'.format(found_const['Id'], t['Amount'], t['Amount'])
    found_trans = get('transactions?{}'.format(query_str))

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
      transactionCreate = post_json('transaction', t)
      logging.debug('STATUS: constituent exists, new transaction')              
      logging.debug(transactionCreate)
      return           

  logging.debug('STATUS: constituent exists, transaction exists')
