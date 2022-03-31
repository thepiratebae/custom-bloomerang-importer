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
    logging.debug(constituentSearch)
    if constituentSearch['ResultCount'] == 0:
        constituentCreate = Bloomerang.post_json('constituent', c)
        logging.debug(constituentCreate)        

        t['AccountId'] = constituentCreate['Id']
        transactionCreate = Bloomerang.post_json('transaction', t)
        logging.debug(transactionCreate)
