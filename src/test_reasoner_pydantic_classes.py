#!/bin/env python3
import gzip
import json
import os
import sys
import timeit
from datetime import datetime

datetime_now = str(datetime.now())
print(f"INFO: {datetime_now}: Starting import of Reasoner Pydantic classes")
t0 = timeit.default_timer()
import reasoner_pydantic
t1 = timeit.default_timer()

datetime_now = str(datetime.now())
print(f"INFO: {datetime_now}: Import complete in {t1-t0} seconds")

files_to_test = [ '../data/exampleTrapi/small.json', '../data/exampleTrapi/medium.json', '../data/exampleTrapi/large.json.gz' ]

for response_file_name in files_to_test:
    t0 = timeit.default_timer()
    print(f"INFO: {datetime_now}: Starting read of local JSON file {response_file_name} of size {os.path.getsize(response_file_name)/1024/1024} MB")
    if response_file_name.endswith('.gz'):
        with gzip.open(response_file_name, 'rt', encoding='utf-8') as infile:
            response_dict = json.load(infile)
    else:
        with open(response_file_name) as infile:
            response_dict = json.load(infile)
    t1 = timeit.default_timer()
    print(f"INFO: {datetime_now}: Read JSON file into dicts and lists in {t1-t0} seconds")

    print(f"INFO: {datetime_now}: Have in hand a message with {len(response_dict['message']['results'])} results")

    print(f"INFO: {datetime_now}: Unmarshaling dicts and lists into Reasoner Pydantic objects")
    t0 = timeit.default_timer()
    response = reasoner_pydantic.Query.model_validate(response_dict)
    t1 = timeit.default_timer()

    datetime_now = str(datetime.now())
    print(f"INFO: {datetime_now}: Reasoner Pydantic objects creation complete in {t1-t0} seconds")

    print(f"INFO: {datetime_now}: Deleting Reasoner Pydantic objects")
    t0 = timeit.default_timer()
    response = None
    t1 = timeit.default_timer()

    datetime_now = str(datetime.now())
    print(f"INFO: {datetime_now}: Reasoner Pydantic objects hierarchy deletion complete in {t1-t0} seconds")
