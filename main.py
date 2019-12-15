import requests
import pprint
import time
import json
import argparse
import aiohttp
import asyncio

import arrow
from jinja2 import Environment, FileSystemLoader

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


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


async def _hydrate_incursion(
    session: aiohttp.ClientSession,
    incursion: dict
) -> dict:

    async def _get_region(region_id: int) -> str:
        full_url = f'{REGIONS}/{region_id}'
        resp = await fetch(session, full_url)
        name = resp.get('name')

        return name

    async def _get_constellation(
        session: aiohttp.ClientSession,
        constellation_id: int
    ) -> dict:
        # TODO: Get the region using the region ID
        full_url = f'{CONSTELLATIONS}/{constellation_id}'
        resp = await fetch(session, full_url)

        new = {}
        new['name'] = resp.get('name')
        new['region_id'] = await _get_region(resp.get('region_id'))

        return new

    async def _get_solar_system(
        session: aiohttp.ClientSession,
        system_id: int
    ) -> dict:
        full_url = f'{SYSTEMS}/{system_id}'
        resp = await fetch(session, full_url)

        new = {}
        new['name'] = resp.get('name')
        new['security_status'] = round(resp.get('security_status'), 1)
        if new['name'].lower() in TYPEMAP.keys():
            new['type'] = TYPEMAP[new['name'].lower()]
        else:
            new['type'] = 'Unknown'

        return new

    async def _get_infested_solar_systems(
        session: aiohttp.ClientSession,
        solar_systems: list
    ) -> list:
        hydrated_list = []
        for x in solar_systems:
            system = await _get_solar_system(session, x)
            hydrated_list.append(system)

        new_list = sorted(hydrated_list, key=lambda x: (x['type']))
        return new_list

    async def _get_faction(session: aiohttp.ClientSession, faction_id: int) -> dict:
        full_url = f'{FACTIONS}'
        resp = await fetch(session, full_url)

        faction = [x for x in resp if x['faction_id'] == faction_id][0]
        return faction.get('name')

    def _handle_influence(influence: float) -> dict:
        return {
            'raw': round(influence, 2) * 100,
            'readable': f'{round(influence, 2) * 100}%'
        }

    def _get_current_time():
        # wraps arrow function just so I can get the timestamp
        # while preserving the command pattern I've got going here.
        return arrow.now().timestamp

    COMMAND_MAP = {
        'constellation_id': lambda x: _get_constellation(session, x),
        'faction_id': lambda x: _get_faction(session, x),
        'staging_solar_system_id': lambda x: _get_solar_system(session, x),
        'infested_solar_systems': lambda x: _get_infested_solar_systems(session, x),
    }

    # NOTE: We need another one because the first one was a mix of std. async
    #       and sync functions. passing it wholesale into a dict comprehension
    #       like I was doing will only result inthe whole thing failing because
    #       we cannot use things like 'bool' with await.
    SYNC_COMMAND_MAP = {
        'has_boss': lambda x: x,
        'influence': _handle_influence,
        'state': lambda x: x.upper()
    }

    print('attempting to hydrate the incursion data')

    new_incursion = {
        k: await COMMAND_MAP[k](v)
        for k, v in incursion.items()
        if k in COMMAND_MAP.keys()
    }

    new_incursion.update({
        k: SYNC_COMMAND_MAP[k](v)
        for k, v in incursion.items()
        if k in SYNC_COMMAND_MAP.keys()
    })

    new_incursion.update({
        'created': _get_current_time()
    })

    return new_incursion


async def get_incursions(from_file=None):

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
            incs = json.loads(F.read())

        pp.pprint(incs)

        return incs
    else:
        print('loading incursions from endpoint...')

        async with aiohttp.ClientSession() as session:
            data = await fetch(session, INCURSIONS)
            # data = requests.get(INCURSIONS).json()

            incursions = [
                await _hydrate_incursion(session, x)
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
    # /Argparse setup

    # Soul
    loop = asyncio.get_event_loop()
    incs = loop.run_until_complete(get_incursions(opts.file))
    # /Soul

    pp.pprint(incs)

    if opts.file is None:
        print('saving updated incursion data...')
        with open(f'incursions-{int(time.time())}.json', 'w') as F:
            F.write(
                json.dumps(incs, indent=2)
            )

    print('Generating index.html file...')
    with open(f'index.html', 'w') as F:
        F.write(
            template.render(
                incursions=incs,
            )
        )

        print('index.html is now available!')
