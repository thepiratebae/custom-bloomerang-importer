import Actblue
import time

data = {
    "csv_type": "paid_contributions",
    "date_range_start": "2022-01-01",
    "date_range_end": "2022-03-15",
}
id = Actblue.post('csvs', data)['id']

resp = Actblue.get('csvs/{}'.format(id))
while resp['status'] != 'complete':
    time.sleep(5)
    resp = Actblue.get('csvs/{}'.format(id))

Actblue.download(resp['download_url'], 'donors.csv')

