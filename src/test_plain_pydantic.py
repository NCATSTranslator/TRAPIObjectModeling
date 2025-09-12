#!/bin/env python3
import gzip
import json
import os
import sys
import timeit
from datetime import datetime


import pydantic
import orjson

print(f"INFO: {datetime.now()}: Starting import of plain pydantic defintions")
t0 = timeit.default_timer()
from plain_pydantic import Response

t1 = timeit.default_timer()

print(f"INFO: {datetime.now()}: Import complete in {t1 - t0} seconds")

files_to_test = [
    "../data/exampleTrapi/small.json",
    "../data/exampleTrapi/medium.json",
    "../data/exampleTrapi/large.json.gz",
]

for response_file_name in files_to_test:
    print(
        f"INFO: {datetime.now()}: Starting read of local JSON file {response_file_name} of size {os.path.getsize(response_file_name) / 1024 / 1024} MB"
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
        f"INFO: {datetime.now()}: Read JSON file into dicts and lists in {t1 - t0} seconds"
    )
    print(
        f"INFO: {datetime.now()}: Have in hand a message with {len(response_dict['message']['results'])} results"
    )

    print(
        f"INFO: {datetime.now()}: Starting ORJSON read of local JSON file {response_file_name} of size {os.path.getsize(response_file_name) / 1024 / 1024} MB"
    )
    t0 = timeit.default_timer()
    if response_file_name.endswith(".gz"):
        with gzip.open(response_file_name, "rt", encoding="utf-8") as infile:
            response_dict = orjson.loads(infile.read())
    else:
        with open(response_file_name) as infile:
            response_dict = orjson.loads(infile.read())
    t1 = timeit.default_timer()
    print(
        f"INFO: {datetime.now()}: Read JSON file into dicts and lists using ORJSON in {t1 - t0} seconds"
    )
    print(
        f"INFO: {datetime.now()}: Have in hand a message with {len(response_dict['message']['results'])} results"
    )

    print(
        f"INFO: {datetime.now()}: Starting Pydantic validation from dicts and lists into plain models"
    )
    t0 = timeit.default_timer()
    response = Response.model_validate(response_dict)
    t1 = timeit.default_timer()
    print(
        f"INFO: {datetime.now()}: Validated dicts and lists into plain models using Pydantic in {t1 - t0} seconds"
    )
    print(
        f"INFO: {datetime.now()}: Have in hand a message with {len(response.message.results)} results"
    )

    print(
        f"INFO: {datetime.now()}: Starting plain model validation using Pydantic directly from local JSON file {response_file_name} of size {os.path.getsize(response_file_name) / 1024 / 1024} MB"
    )
    t0 = timeit.default_timer()
    if response_file_name.endswith(".gz"):
        with gzip.open(response_file_name, "rt", encoding="utf-8") as infile:
            response = Response.model_validate_json(infile.read())
    else:
        with open(response_file_name) as infile:
            response = Response.model_validate_json(infile.read())
    t1 = timeit.default_timer()
    print(
        f"INFO: {datetime.now()}: Read JSON file into dicts and lists in {t1 - t0} seconds"
    )
    print(
        f"INFO: {datetime.now()}: Have in hand a message with {len(response.message.results)} results"
    )

    print(f"INFO: {datetime.now()}: Deleting Dataclass instances")
    t0 = timeit.default_timer()
    response = None
    t1 = timeit.default_timer()
    print(
        f"INFO: {datetime.now()}: Dataclass instance deletion complete in {t1 - t0} seconds"
    )
