import json
import csv
import base64
import gzip
import configparser

import requests
from requests_oauthlib import OAuth1

base_uri = 'https://api.cardmarket.com/ws/v2.0/output.json'


def get_auth(url):
    config = configparser.ConfigParser()
    config.read('../auth.ini')
    app_token = config['app_token']
    app_secret = config['app_secret']
    access_token = config['access_token']
    access_token_secret = config['access_token_secret']
    return OAuth1(app_token, app_secret, access_token, access_token_secret, signature_type='auth_header', realm=url)


def request(method, route, params=None):
    url = base_uri + route
    auth = get_auth(url)
    return requests.request(method, url, auth=auth)


def get_expansions():
    r = request('GET', '/games/1/expansions')
    expansions = json.loads(r.content)['expansion']
    keys = ['idExpansion', 'enName', 'abbreviation']
    sets = [{key: expansion[key] for key in keys} for expansion in expansions]
    with open('expansions.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, keys)
        writer.writeheader()
        writer.writerows(sets)


def read_expansions():
    with open('expansions.csv', 'r') as file:
        reader = csv.DictReader(file)
        key_map = {
            'enName': 'name',
            'idExpansion': 'id',
            'abbreviation': 'abbreviation'
        }
        expansions = {}
        for row in reader:
            expansions[row['enName']] = {
                key_map[key]: int(row[key]) if row[key].isdigit() else row[key] for key in key_map.keys()}
        return expansions


def get_product_list():
    r = request('GET', '/productlist')
    encoded = json.loads(r.content)['productsfile'].encode('utf-8')
    decoded = base64.decodebytes(encoded)
    unzipped = gzip.decompress(decoded)
    with open('products.csv', mode='wb') as file:
        file.write(unzipped)


def read_product_list():
    with open('products.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        key_map = {
            'idProduct': 'id',
            'Name': 'name',
            'Expansion ID': 'expansionId'
        }
        products = {}
        for row in reader:
            if row['Category ID'] == '1' and row['Expansion ID']:
                products[(row['Name'], int(row['Expansion ID']))] = {
                    key_map[key]: int(row[key]) if row[key].isdigit() else row[key] for key in key_map.keys()}
        return products


def read_inventory():
    with open('inventory.csv', newline='') as file:
        reader = csv.DictReader(file)
        key_map = {
            'Count': 'count',
            'Name': 'name',
            'Edition': 'expansion',
            'Foil': 'foil',
            'Price': 'price',
            'Condition': 'condition',
            'Language': 'language'
        }
        cards = []
        for row in reader:
            if row['Condition'] != 'Poor':
                card = {key_map[key]: int(row[key]) if row[key].isdigit() else row[key] for key in key_map.keys()}
                card['price'] = float(card['price'].strip('$'))
                cards.append(card)
        return cards


def get_mkm_pricing(items):
    for item in items:
        r = request('GET', '/products/{}'.format(item['product']['id']))
        item['product_detail'] = json.loads(r.content)
        print(json.dumps(item, indent=2))

    with open('data.json', 'w') as file:
        json.dump(items, file)


def read_mkm_pricing():
    with open('data.json', 'r') as file:
        items = json.load(file)
    return items


def match_items():
    i = read_inventory()
    e = read_expansions()
    p = read_product_list()

    found_items = []
    for item in i:
        expansion = e.get(item['expansion'], None)
        if expansion:
            item['expansion_info'] = expansion
            product = p.get((item['name'], expansion['id']), None)
            if product:
                item['product'] = product
                found_items.append(item)


def main():
    items = read_mkm_pricing()
    print(json.dumps(items, indent=2))


if __name__ == '__main__':
    main()
