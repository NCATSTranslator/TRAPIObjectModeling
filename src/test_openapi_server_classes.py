#!/bin/env python3
import sys
import os

import timeit
from datetime import datetime
import requests
import json
import gzip

datetime_now = str(datetime.now())
print(f"INFO: {datetime_now}: Starting import of OpenAPI classes")
t0 = timeit.default_timer()
from openapi_server.models.analysis import Analysis
from openapi_server.models.analysis_all_of import AnalysisAllOf
from openapi_server.models.async_query import AsyncQuery
from openapi_server.models.async_query_response import AsyncQueryResponse
from openapi_server.models.async_query_status_response import AsyncQueryStatusResponse
from openapi_server.models.attribute import Attribute
from openapi_server.models.attribute_constraint import AttributeConstraint
from openapi_server.models.auxiliary_graph import AuxiliaryGraph
from openapi_server.models.base_analysis import BaseAnalysis
from openapi_server.models.base_query_graph import BaseQueryGraph
from openapi_server.models.edge import Edge
from openapi_server.models.edge_binding import EdgeBinding
from openapi_server.models.entity_query import EntityQuery
from openapi_server.models.knowledge_graph import KnowledgeGraph
from openapi_server.models.log_entry import LogEntry
from openapi_server.models.log_level import LogLevel
from openapi_server.models.mesh_ngd_response import MeshNgdResponse
from openapi_server.models.message import Message
from openapi_server.models.meta_attribute import MetaAttribute
from openapi_server.models.meta_edge import MetaEdge
from openapi_server.models.meta_knowledge_graph import MetaKnowledgeGraph
from openapi_server.models.meta_node import MetaNode
from openapi_server.models.meta_qualifier import MetaQualifier
from openapi_server.models.node import Node
from openapi_server.models.node_binding import NodeBinding
from openapi_server.models.operation_annotate import OperationAnnotate
from openapi_server.models.operation_annotate_edges import OperationAnnotateEdges
from openapi_server.models.operation_annotate_edges_parameters import OperationAnnotateEdgesParameters
from openapi_server.models.operation_annotate_nodes import OperationAnnotateNodes
from openapi_server.models.operation_annotate_nodes_parameters import OperationAnnotateNodesParameters
from openapi_server.models.operation_bind import OperationBind
from openapi_server.models.operation_complete_results import OperationCompleteResults
from openapi_server.models.operation_enrich_results import OperationEnrichResults
from openapi_server.models.operation_enrich_results_parameters import OperationEnrichResultsParameters
from openapi_server.models.operation_fill import OperationFill
from openapi_server.models.operation_filter_kgraph import OperationFilterKgraph
from openapi_server.models.operation_filter_kgraph_continuous_kedge_attribute import OperationFilterKgraphContinuousKedgeAttribute
from openapi_server.models.operation_filter_kgraph_continuous_kedge_attribute_parameters import OperationFilterKgraphContinuousKedgeAttributeParameters
from openapi_server.models.operation_filter_kgraph_discrete_kedge_attribute import OperationFilterKgraphDiscreteKedgeAttribute
from openapi_server.models.operation_filter_kgraph_discrete_kedge_attribute_parameters import OperationFilterKgraphDiscreteKedgeAttributeParameters
from openapi_server.models.operation_filter_kgraph_discrete_knode_attribute import OperationFilterKgraphDiscreteKnodeAttribute
from openapi_server.models.operation_filter_kgraph_discrete_knode_attribute_parameters import OperationFilterKgraphDiscreteKnodeAttributeParameters
from openapi_server.models.operation_filter_kgraph_orphans import OperationFilterKgraphOrphans
from openapi_server.models.operation_filter_kgraph_percentile import OperationFilterKgraphPercentile
from openapi_server.models.operation_filter_kgraph_percentile_parameters import OperationFilterKgraphPercentileParameters
from openapi_server.models.operation_filter_kgraph_std_dev import OperationFilterKgraphStdDev
from openapi_server.models.operation_filter_kgraph_std_dev_parameters import OperationFilterKgraphStdDevParameters
from openapi_server.models.operation_filter_kgraph_top_n import OperationFilterKgraphTopN
from openapi_server.models.operation_filter_kgraph_top_n_parameters import OperationFilterKgraphTopNParameters
from openapi_server.models.operation_filter_results import OperationFilterResults
from openapi_server.models.operation_filter_results_top_n import OperationFilterResultsTopN
from openapi_server.models.operation_filter_results_top_n_parameters import OperationFilterResultsTopNParameters
from openapi_server.models.operation_lookup import OperationLookup
from openapi_server.models.operation_lookup_and_score import OperationLookupAndScore
from openapi_server.models.operation_overlay import OperationOverlay
from openapi_server.models.operation_overlay_compute_jaccard import OperationOverlayComputeJaccard
from openapi_server.models.operation_overlay_compute_jaccard_parameters import OperationOverlayComputeJaccardParameters
from openapi_server.models.operation_overlay_compute_ngd import OperationOverlayComputeNgd
from openapi_server.models.operation_overlay_compute_ngd_parameters import OperationOverlayComputeNgdParameters
from openapi_server.models.operation_overlay_connect_knodes import OperationOverlayConnectKnodes
from openapi_server.models.operation_overlay_fisher_exact_test import OperationOverlayFisherExactTest
from openapi_server.models.operation_overlay_fisher_exact_test_parameters import OperationOverlayFisherExactTestParameters
from openapi_server.models.operation_restate import OperationRestate
from openapi_server.models.operation_score import OperationScore
from openapi_server.models.operation_sort_results import OperationSortResults
from openapi_server.models.operation_sort_results_edge_attribute import OperationSortResultsEdgeAttribute
from openapi_server.models.operation_sort_results_edge_attribute_parameters import OperationSortResultsEdgeAttributeParameters
from openapi_server.models.operation_sort_results_node_attribute import OperationSortResultsNodeAttribute
from openapi_server.models.operation_sort_results_node_attribute_parameters import OperationSortResultsNodeAttributeParameters
from openapi_server.models.operation_sort_results_score import OperationSortResultsScore
from openapi_server.models.operation_sort_results_score_parameters import OperationSortResultsScoreParameters
from openapi_server.models.operations import Operations
from openapi_server.models.path_binding import PathBinding
from openapi_server.models.path_constraint import PathConstraint
from openapi_server.models.pathfinder_analysis import PathfinderAnalysis
from openapi_server.models.pathfinder_analysis_all_of import PathfinderAnalysisAllOf
from openapi_server.models.pathfinder_query_graph import PathfinderQueryGraph
from openapi_server.models.pathfinder_query_graph_all_of import PathfinderQueryGraphAllOf
from openapi_server.models.q_edge import QEdge
from openapi_server.models.q_node import QNode
from openapi_server.models.q_path import QPath
from openapi_server.models.qualifier import Qualifier
from openapi_server.models.qualifier_constraint import QualifierConstraint
from openapi_server.models.query import Query
from openapi_server.models.query_graph import QueryGraph
from openapi_server.models.query_graph_all_of import QueryGraphAllOf
from openapi_server.models.question import Question
from openapi_server.models.resource_role_enum import ResourceRoleEnum
from openapi_server.models.response import Response
from openapi_server.models.result import Result
from openapi_server.models.retrieval_source import RetrievalSource
t1 = timeit.default_timer()

datetime_now = str(datetime.now())
print(f"INFO: {datetime_now}: Import complete in {t1-t0} seconds")

files_to_test = [ '../data/exampleTrapi/small.json', '../data/exampleTrapi/medium.json', '../data/exampleTrapi/large.json.gz' ]

for response_file_name in files_to_test:
    t0 = timeit.default_timer()
    if os.path.exists(response_file_name):
        print(f"INFO: {datetime_now}: Starting read of local JSON file {response_file_name} of size {os.path.getsize(response_file_name)/1024/1024} MB")
        if response_file_name.endswith('.gz'):
            with gzip.open(response_file_name, 'rt', encoding='utf-8') as infile:
                response_dict = json.load(infile)
        else:
            with open(response_file_name) as infile:
                response_dict = json.load(infile)
        t1 = timeit.default_timer()
        print(f"INFO: {datetime_now}: Read JSON file into dicts and lists in {t1-t0} seconds")

    else:
        print(f"ERROR: Unable to find test file {response_file_name}. Code to download data is disabled")
        exit()
        response_id = '354033'
        #response_id = '3750385e-61b4-405e-ad0d-09845ea0c545'
        endpoint_url = f"https://arax.ncats.io/beta/api/arax/v1.4/response/{response_id}"
        print(f"INFO: {datetime_now}: Starting download of response from arax.ncats.io")
        response_content = requests.get(endpoint_url, headers={'accept': 'application/json'})
        status_code = response_content.status_code
        if status_code != 200:
            print("ERROR returned with status "+str(status_code))
            print(response_content)
            exit()
        t1 = timeit.default_timer()
        print(f"INFO: {datetime_now}: Downloaded example response of size {len(response_content.text)} in {t1-t0} seconds")

        t0 = timeit.default_timer()
        response_dict = response_content.json()
        t1 = timeit.default_timer()
        print(f"INFO: {datetime_now}: Converted text to dicts and lists in {t1-t0} seconds")

        with open(response_file_name, 'w') as outfile:
            json.dump(response_dict, outfile, indent=4)

    print(f"INFO: {datetime_now}: Have in hand a message with {len(response_dict['message']['results'])} results")

    print(f"INFO: {datetime_now}: Unmarshaling dicts and lists into OpenAPI objects")
    t0 = timeit.default_timer()
    response = Response().from_dict(response_dict)
    t1 = timeit.default_timer()

    datetime_now = str(datetime.now())
    print(f"INFO: {datetime_now}: OpenAPI objects creation complete in {t1-t0} seconds")

    print(f"INFO: {datetime_now}: Deleting OpenAPI objects")
    t0 = timeit.default_timer()
    response = None
    t1 = timeit.default_timer()

    datetime_now = str(datetime.now())
    print(f"INFO: {datetime_now}: OpenAPI objects hierarchy deletion complete in {t1-t0} seconds")






