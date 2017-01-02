import io
import csv
import json

import requests
import click
import backoff

DIVISION_BOUNDARY_FILE_URL = 'http://data.phl.opendata.arcgis.com/datasets/160a3665943d4864806d7b1399029a04_0.geojson'
VOTER_REGISTRATION_FILE_URL = 'https://data.phila.gov/api/views/g4jp-m82n/rows.csv?accessType=DOWNLOAD'
VOTER_TURNOUT_FILE_URL = 'https://data.phila.gov/api/views/fpmf-whei/rows.csv?accessType=DOWNLOAD'

def fatal_code(e):
    if e.response and e.response.status_code:
        return 400 <= e.response.status_code < 500

@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException,
                       requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError),
                      max_tries=5,
                      giveup=fatal_code,
                      factor=2)
def get_division_polling_place(ward_division_num):
    return requests.get('http://api.phila.gov:80/polling-places/v1/',
                        params={'ward': ward_division_num[0:2],
                                'division': ward_division_num[2:]}).json()

def pad(num):
    return str(num).zfill(2)

@click.command()
@click.option('--output-file',
              default='Political_Divisions_Voter_Stats.geojson',
              help='Output GeoJSON file path.')
def main(output_file):
    click.echo('Pulling and preparing registration and turnout data')

    voter_registration_stats_response = requests.get(VOTER_REGISTRATION_FILE_URL)
    voter_registration_stats = {}
    for row in csv.DictReader(io.StringIO(voter_registration_stats_response.text)):
        voter_registration_stats[pad(row['Ward']) + pad(row['Division'])] = row['Total']

    voter_turnout_stats_response = requests.get(VOTER_TURNOUT_FILE_URL)
    voter_turnout_stats = {}
    for row in csv.DictReader(io.StringIO(voter_turnout_stats_response.text)):
        if row['Precinct Code'] not in voter_turnout_stats:
            voter_turnout_stats[row['Precinct Code']] = int(row['Voter Count'])
        else:
            voter_turnout_stats[row['Precinct Code']] += int(row['Voter Count'])

    division_boundaries = requests.get(DIVISION_BOUNDARY_FILE_URL).json()

    total_str = str(len(division_boundaries['features']))
    count = 1
    for feature in division_boundaries['features']:
        ward_division_num = feature['properties']['DIVISION_NUM']
        feature['properties']['WARD_NUM'] = ward_division_num[0:2]
        feature['properties']['REGISTRATION_TOTAL'] = voter_registration_stats[ward_division_num]
        feature['properties']['TURNOUT_TOTAL'] = voter_turnout_stats[ward_division_num]

        click.echo('Looking up ' + ward_division_num + ' polling address - ' + str(count) + '/' + total_str)
        count += 1

        polling_place = get_division_polling_place(ward_division_num)
        polling_address = polling_place['features'][0]['attributes']['display_address']
        feature['properties']['POLLING_PLACE_ADDRESS'] = polling_address
        
        click.echo(polling_address)

    with open(output_file, 'w') as out:
        json.dump(division_boundaries, out)

if __name__ == "__main__":
    main()
