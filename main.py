import requests
import pprint
import json
import bson
import time
import argparse

import arrow
from jinja2 import Environment, FileSystemLoader, select_autoescape

from type_map import TYPEMAP

pp = pprint.PrettyPrinter(indent=2)


BASE_ENDPOINT = 'https://esi.evetech.net/latest'
INCURSIONS = f'{BASE_ENDPOINT}/incursions'
CONSTELLATIONS = f'{BASE_ENDPOINT}/universe/constellations'
# NOTE: just pull the faction out of the response json.
FACTIONS = f'{BASE_ENDPOINT}/universe/factions'
SYSTEMS = f'{BASE_ENDPOINT}/universe/systems'
REGIONS = f'{BASE_ENDPOINT}/universe/regions'


# SAMPLE OUTPUT
# { 'constellation_id': 20000735,
#     'faction_id': 500019,
#     'has_boss': True,
#     'infested_solar_systems': [ 30005024,
#                                 30005025,
#                                 30005026,
#                                 30005027,
#                                 30005028,
#                                 30005029,
#                                 30024971],
#     'influence': 0.928166655699412,
#     'staging_solar_system_id': 30005028,
#     'state': 'established',
#     'type': 'Incursion'},


def _hydrate_incursion(incursion: dict) -> dict:
    def _get_region(region_id: int) -> str:
        full_url = f'{REGIONS}/{region_id}'

        resp = requests.get(full_url).json()

        name = resp.get('name')

        return name

    def _get_constellation(constellation_id: int) -> dict:
        # TODO: Get the region using the region ID
        full_url = f'{CONSTELLATIONS}/{constellation_id}'
        resp = requests.get(full_url).json()

        new = {}
        new['name'] = resp.get('name')
        new['region_id'] = _get_region(resp.get('region_id'))

        return new

    def _get_solar_system(system_id: int) -> dict:
        full_url = f'{SYSTEMS}/{system_id}'
        resp = requests.get(full_url)

        new = {}
        new['name'] = resp.json().get('name')
        new['security_status'] = round(resp.json().get('security_status'), 1)
        if new['name'].lower() in TYPEMAP.keys():
            new['type'] = TYPEMAP[new['name'].lower()]
        else:
            new['type'] = 'Unknown'

        return new

    def _get_infested_solar_systems(solar_systems: list) -> list:
        hydrated_list = []
        for x in solar_systems:
            hydrated_list.append(_get_solar_system(x))

        return hydrated_list

    def _get_faction(faction_id: int) -> dict:
        full_url = f'{FACTIONS}'
        resp = requests.get(full_url).json()

        faction = [x for x in resp if x['faction_id'] == faction_id][0]
        return faction.get('name')

    def _get_current_time():
        # wraps arrow function just so I can get the timestamp
        # while preserving the command pattern I've got going here.
        return arrow.now().timestamp

    COMMAND_MAP = {
        'constellation_id': _get_constellation,
        'faction_id': _get_faction,
        'staging_solar_system_id': _get_solar_system,
        'infested_solar_systems': _get_infested_solar_systems,
        'has_boss': lambda x: x,
        'influence': lambda x: f'{(round(x, 2) * 100)}%',
        'state': lambda x: x
    }

    print('attempting to hydrate the incursion data')

    incursion = {
        k: COMMAND_MAP[k](v)
        for k, v in incursion.items()
        if k in COMMAND_MAP.keys()
    }

    incursion.update({
        'created': _get_current_time()
    })

    return incursion


def get_incursions(from_file=None):

    # standard incursion storage format v1:
    # {
    #   "hs": [{...}, {...}],
    #   "ls": [{...}, {...}],
    #   "ns": [{...}, {...}],
    # }
    print('Getting the latest incursion data...')

    if from_file:
        print('loading from file...')
        with open(opts.file, 'rb') as F:
            incs = bson.loads(F.read())

        pp.pprint(incs)

        return incs
    else:
        print('loading incursions from endpoint...')

        data = requests.get(INCURSIONS).json()

        pp.pprint(data)

        incursions = [
            _hydrate_incursion(x)
            for x in data
        ]

        output = {
            'hs': [
                x for x in incursions
                if x['staging_solar_system_id']['security_status'] >= 0.5
            ],
            'ls': [
                x for x in incursions
                if x['staging_solar_system_id']['security_status'] > 0
                and x['staging_solar_system_id']['security_status'] < 0.5
            ],
            'ns': [
                x for x in incursions
                if x['staging_solar_system_id']['security_status'] <= 0
            ]
        }

        return output


if __name__ == '__main__':
    # Jinja2 Setup
    env = Environment(
        loader=FileSystemLoader('./templates'),
        # autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('_template.html')
    # /Jinja2 Setup

    # Argparse setup
    parser = argparse.ArgumentParser(
        description='This generates the index page for Incursion Watch V2',
    )
    parser.add_argument(
        '--file',
        type=str,
        help='specifies a file to load from.',
        default=None
    )
    opts = parser.parse_args()
    # Argparse setup

    if opts.file:
        print(f'Opening file {opts.file} to retrieve incursion data...')
        incs = get_incursions(opts.file)

    else:
        print('No file specified, pinging the API for the updated data...')
        incs = get_incursions(None)

        print('saving updated incursion data...')
        with open(f'incursions-{int(time.time())}.bson', 'wb') as F:
            F.write(
                bson.dumps(incs)
            )

    print('Generating index.html file...')
    with open(f'index.html', 'w') as F:
        F.write(
            template.render(
                incursions=incs,
            )
        )

        print('index.html is now available!')
