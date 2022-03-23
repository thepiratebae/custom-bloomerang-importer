import Actblue
import Bloomerang
import time

from datetime import date
today = date.today().strftime("%Y-%m-%d")

ab_json = Actblue.get_contributions('2022-01-01', today)


#map ab fields to bloomerang fields
constituents = []
transactions = []
for ab_transaction in ab_json:
    constituent = {}
    constituent['FirstName'] = ab_transaction['Donor First Name']
    constituent['LastName'] = ab_transaction['Donor Last Name']
    constituent['Employer'] = ab_transaction['Donor Employer']
    constituent['PrimaryAddress']['Street'] = ab_transaction['Donor Addr1']
    constituent['PrimaryAddress']['City'] = ab_transaction['Donor City']
    constituent['PrimaryAddress']['State'] = ab_transaction['Donor State']
    constituent['PrimaryAddress']['PostalCode'] = ab_transaction['Donor ZIP']
    constituent['PrimaryAddress']['Country'] = ab_transaction['Donor Country']
    constituent['JobTitle'] = ab_transaction['Donor Occupation']
    constituent['PrimaryEmail']['Value'] = ab_transaction['Donor Email']
    constituent['PrimaryPhone']['Number'] = ab_transaction['Donor Phone']
    constituents.append(constituent)

    #not sure right now how to map transactions to their donors?
    # transaction = {}
    # transaction['Date'] = ab_transaction['Date']
    # transaction['Amount'] = ab_transaction['Date']

# resp = Bloomerang.get('constituents?take=10')
# resp = Bloomerang.get('transactions?take=10')
# print(resp)