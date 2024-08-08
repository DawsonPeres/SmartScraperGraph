# -*- coding: utf-8 -*-

"""
Custom BaseGraph Module
"""

import time
from langchain_community.callbacks import get_openai_callback
from typing import Tuple

from scrapegraphai.graphs import BaseGraph
from scrapegraphai.telemetry import log_graph_execution


class MyBaseGraph(BaseGraph):

    def __init__(self, nodes: list, edges: list, entry_point: str, use_burr: bool = False, burr_config: dict = None,
                 graph_name: str = "Custom"):
        super().__init__(nodes, edges, entry_point, use_burr, burr_config, graph_name)

    def _execute_standard(self, initial_state: dict) -> Tuple[dict, list]:
        current_node_name = self.entry_point
        state = initial_state

        total_exec_time = 0.0
        exec_info = []
        cb_total = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "successful_requests": 0,
            "total_cost_USD": 0.0,
        }

        start_time = time.time()
        error_node = None
        source_type = None
        llm_model = None
        embedder_model = None
        source = []
        prompt = None
        schema = None

        while current_node_name:
            curr_time = time.time()
            current_node = next(node for node in self.nodes if node.node_name == current_node_name)

            # check if there is a "source" key in the node config
            if current_node.__class__.__name__ in ["FetchNode", "MyFetchNode"]:
                # get the second key name of the state dictionary
                source_type = list(state.keys())[1]
                if state.get("user_prompt", None):
                    prompt = state["user_prompt"] if type(state["user_prompt"]) == str else None
                # quick fix for local_dir source type
                if source_type == "local_dir":
                    source_type = "html_dir"
                elif source_type == "url":
                    if type(state[source_type]) == list:
                        # iterate through the list of urls and see if they are strings
                        for url in state[source_type]:
                            if type(url) == str:
                                source.append(url)
                    elif type(state[source_type]) == str:
                        source.append(state[source_type])

            # check if there is an "llm_model" variable in the class
            if hasattr(current_node, "llm_model") and llm_model is None:
                llm_model = current_node.llm_model
                if hasattr(llm_model, "model_name"):
                    llm_model = llm_model.model_name
                elif hasattr(llm_model, "model"):
                    llm_model = llm_model.model

            # check if there is an "embedder_model" variable in the class
            if hasattr(current_node, "embedder_model") and embedder_model is None:
                embedder_model = current_node.embedder_model
                if hasattr(embedder_model, "model_name"):
                    embedder_model = embedder_model.model_name
                elif hasattr(embedder_model, "model"):
                    embedder_model = embedder_model.model

            if hasattr(current_node, "node_config"):
                if type(current_node.node_config) is dict:
                    if current_node.node_config.get("schema", None) and schema is None:
                        if type(current_node.node_config["schema"]) is not dict:
                            # convert to dict
                            try:
                                schema = current_node.node_config["schema"].schema()
                            except Exception as e:
                                schema = None

            with get_openai_callback() as cb:
                try:
                    result = current_node.execute(state)
                except Exception as e:
                    error_node = current_node.node_name

                    graph_execution_time = time.time() - start_time
                    log_graph_execution(
                        graph_name=self.graph_name,
                        source=source,
                        prompt=prompt,
                        schema=schema,
                        llm_model=llm_model,
                        embedder_model=embedder_model,
                        source_type=source_type,
                        execution_time=graph_execution_time,
                        error_node=error_node,
                        exception=str(e)
                    )
                    raise e
                node_exec_time = time.time() - curr_time
                total_exec_time += node_exec_time

                cb_data = {
                    "node_name": current_node.node_name,
                    "total_tokens": cb.total_tokens,
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "successful_requests": cb.successful_requests,
                    "total_cost_USD": cb.total_cost,
                    "exec_time": node_exec_time,
                }

                exec_info.append(cb_data)

                cb_total["total_tokens"] += cb_data["total_tokens"]
                cb_total["prompt_tokens"] += cb_data["prompt_tokens"]
                cb_total["completion_tokens"] += cb_data["completion_tokens"]
                cb_total["successful_requests"] += cb_data["successful_requests"]
                cb_total["total_cost_USD"] += cb_data["total_cost_USD"]

            if current_node.node_type == "conditional_node":
                current_node_name = result
            elif current_node_name in self.edges:
                current_node_name = self.edges[current_node_name]
            else:
                current_node_name = None

        exec_info.append({
            "node_name": "TOTAL RESULT",
            "total_tokens": cb_total["total_tokens"],
            "prompt_tokens": cb_total["prompt_tokens"],
            "completion_tokens": cb_total["completion_tokens"],
            "successful_requests": cb_total["successful_requests"],
            "total_cost_USD": cb_total["total_cost_USD"],
            "exec_time": total_exec_time,
        })

        # Log the graph execution telemetry
        graph_execution_time = time.time() - start_time
        response = state.get("answer", None) if source_type == "url" else None
        content = state.get("parsed_doc", None) if response is not None else None

        log_graph_execution(
            graph_name=self.graph_name,
            source=source,
            prompt=prompt,
            schema=schema,
            llm_model=llm_model,
            embedder_model=embedder_model,
            source_type=source_type,
            content=content,
            response=response,
            execution_time=graph_execution_time,
            total_tokens=cb_total["total_tokens"] if cb_total["total_tokens"] > 0 else None,
        )

        return state, exec_info

    # def execute(self, initial_state: dict) -> Tuple[dict, list]:
    #     self.initial_state = initial_state
    #     if self.use_burr:
    #         from scrapegraphai.integrations import BurrBridge
    #
    #         bridge = BurrBridge(self, self.burr_config)
    #         result = bridge.execute(initial_state)
    #         return (result["_state"], [])
    #     else:
    #         return self._execute_standard(initial_state)
