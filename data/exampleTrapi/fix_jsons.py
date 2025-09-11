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

# files_to_test = [ './small.json', './medium.json', './large.json.gz' ]
files_to_test = [ './medium.json' ]

for response_file_name in files_to_test:
    t0 = timeit.default_timer()
    print(f"INFO: {datetime_now}: Starting read of local JSON file {response_file_name} of size {os.path.getsize(response_file_name)/1024/1024} MB")
    if response_file_name.endswith('.gz'):
        with gzip.open(response_file_name, 'rt', encoding='utf-8') as infile:
            response_dict = json.load(infile)
    else:
        with open(response_file_name) as infile:
            response_dict = json.load(infile)

    for aux_graph in response_dict["message"]["auxiliary_graphs"].values():
        aux_graph["attributes"] = aux_graph.get("attributes", [])
    for result in response_dict["message"]["results"]:
        for analysis in result["analyses"]:
            for edge_bindings in analysis["edge_bindings"].values():
                for edge_binding in edge_bindings:
                    edge_binding["attributes"] = edge_binding.get("attributes", [])
        for node_bindings in result["node_bindings"].values():
            for node_binding in node_bindings:
                node_binding["attributes"] = node_binding.get("attributes", [])
    for node in response_dict["message"]["knowledge_graph"]["nodes"].values():
        node["attributes"] = node.get("attributes", [])

    if not response_file_name.endswith(".gz"):
        with open(response_file_name, "w", encoding="utf-8") as outfile:
            json.dump(response_dict, outfile)
