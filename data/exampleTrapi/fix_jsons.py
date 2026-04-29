#!/bin/env python3
import datetime
import gzip
import re
import timeit
from pathlib import Path

import orjson

main_dir = Path(__file__).parent.resolve()

datetime_now = str(datetime.datetime.now())
t0 = timeit.default_timer()
t1 = timeit.default_timer()

datetime_now = str(datetime.datetime.now())

files_to_test = ["./small.json", "./medium.json", "./large.json.gz"]
# files_to_test = ["./medium.json"]

for response_file_name in files_to_test:
    t0 = timeit.default_timer()
    response_path = main_dir / response_file_name
    print(
        f"INFO: {datetime_now}: Starting read of local JSON file {response_path} of size {response_path.stat().st_size / 1024 / 1024} MB"
    )
    if response_path.suffix.endswith(".gz"):
        with gzip.open(response_path, "rt", encoding="utf-8") as infile:
            response_dict = orjson.loads(infile.read())
    else:
        with response_path.open() as infile:
            response_dict = orjson.loads(infile.read())

    for aux_graph in response_dict["message"]["auxiliary_graphs"].values():
        aux_graph["attributes"] = aux_graph.get("attributes", [])
    for result in response_dict["message"]["results"]:
        for analysis in result["analyses"]:
            if "edge_bindings" in analysis:
                for edge_bindings in analysis["edge_bindings"].values():
                    for edge_binding in edge_bindings:
                        edge_binding["attributes"] = edge_binding.get("attributes", [])
        for node_bindings in result["node_bindings"].values():
            for node_binding in node_bindings:
                node_binding["attributes"] = node_binding.get("attributes", [])
    for node in response_dict["message"]["knowledge_graph"]["nodes"].values():
        node["attributes"] = node.get("attributes", [])

    time_pattern = re.compile(r"\d{2}:\d{2}:\d{2}")

    if "logs" in response_dict:
        for log in response_dict["logs"]:
            if time_pattern.match(log["timestamp"]):
                new_dt = datetime.datetime.fromisoformat(
                    f"{datetime.date.today()}T{log['timestamp']}"
                )
                log["timestamp"] = new_dt.astimezone().isoformat()
            # Ensure TZ-aware
            log["timestamp"] = (
                datetime.datetime.fromisoformat(log["timestamp"])
                .astimezone()
                .isoformat()
            )

    if not response_path.suffix.endswith(".gz"):
        with response_path.open("wb") as outfile:
            outfile.write(orjson.dumps(response_dict))
    else:
        with gzip.open(response_path, "wb") as outfile:
            outfile.write(orjson.dumps(response_dict))
