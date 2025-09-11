#!/bin/env python3
import gzip
import json
import os
import sys
import timeit
from datetime import datetime


import pydantic

datetime_now = str(datetime.now())
print(f"INFO: {datetime_now}: Starting import of TypedDict defintions")
t0 = timeit.default_timer()
from typeddict import Response

t1 = timeit.default_timer()

datetime_now = str(datetime.now())
print(f"INFO: {datetime_now}: Import complete in {t1 - t0} seconds")

files_to_test = [
    "../data/exampleTrapi/small.json",
    "../data/exampleTrapi/medium.json",
    "../data/exampleTrapi/large.json.gz",
]

for response_file_name in files_to_test:
    print(
        f"INFO: {datetime_now}: Starting read of local JSON file {response_file_name} of size {os.path.getsize(response_file_name) / 1024 / 1024} MB"
    )
    t0 = timeit.default_timer()
    if response_file_name.endswith(".gz"):
        with gzip.open(response_file_name, "rt", encoding="utf-8") as infile:
            response_dict = json.load(infile)
    else:
        with open(response_file_name) as infile:
            response_dict = json.load(infile)
    t1 = timeit.default_timer()
    print(
        f"INFO: {datetime_now}: Read JSON file into dicts and lists in {t1 - t0} seconds"
    )

    print(
        f"INFO: {datetime_now}: Have in hand a message with {len(response_dict['message']['results'])} results"
    )

    print(
        f"INFO: {datetime_now}: Unmarshaling dicts and lists into TypedDict and lists"
    )
    t0 = timeit.default_timer()
    response = Response(response_dict)
    t1 = timeit.default_timer()

    datetime_now = str(datetime.now())
    print(f"INFO: {datetime_now}: TypedDict creation complete in {t1 - t0} seconds")

    print(f"INFO: {datetime_now}: Deleting TypeDict instances")
    t0 = timeit.default_timer()
    response = None
    t1 = timeit.default_timer()

    datetime_now = str(datetime.now())
    print(
        f"INFO: {datetime_now}: TypedDict instance deletion complete in {t1 - t0} seconds"
    )

    print(
        f"INFO: {datetime_now}: Starting pydantic-to-TypedDict validation of local JSON file {response_file_name} of size {os.path.getsize(response_file_name) / 1024 / 1024} MB"
    )
    adapter = pydantic.TypeAdapter(Response)
    t0 = timeit.default_timer()
    if response_file_name.endswith(".gz"):
        with gzip.open(response_file_name, "rt", encoding="utf-8") as infile:
            respose_dict = adapter.validate_json(infile.read())
    else:
        with open(response_file_name) as infile:
            respose_dict = adapter.validate_json(infile.read())
    t1 = timeit.default_timer()
    print(
        f"INFO: {datetime_now}: Read JSON file into dicts and lists in {t1 - t0} seconds"
    )
    print(
        f"INFO: {datetime_now}: Have in hand a message with {len(response_dict['message']['results'])} results"
    )

