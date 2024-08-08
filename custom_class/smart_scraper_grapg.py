# -*- coding: utf-8 -*-

"""
Custom SmartScraperGraph Module
"""

from typing import Optional
from pydantic import BaseModel
from scrapegraphai.graphs import SmartScraperGraph

from scrapegraphai.nodes import (
    ParseNode,
    GenerateAnswerNode
)

from custom_class.base_graph import MyBaseGraph
from custom_class.fetch_node import MyFetchNode


class MySmartScraperGraph(SmartScraperGraph):

    def __init__(self, prompt: str, source: str, config: dict, schema: Optional[BaseModel] = None):
        super().__init__(prompt, source, config, schema)

    def _create_graph(self) -> MyBaseGraph:
        fetch_node = MyFetchNode(
            input="url| local_dir",
            output=["doc", "link_urls", "img_urls"],
            node_config={
                "llm_model": self.llm_model,
                "force": self.config.get("force", False),
                "cut": self.config.get("cut", True),
                "loader_kwargs": self.config.get("loader_kwargs", {}),
            }
        )
        parse_node = ParseNode(
            input="doc",
            output=["parsed_doc"],
            node_config={
                "chunk_size": self.model_token
            }
        )

        generate_answer_node = GenerateAnswerNode(
            input="user_prompt & (relevant_chunks | parsed_doc | doc)",
            output=["answer"],
            node_config={
                "llm_model": self.llm_model,
                "additional_info": self.config.get("additional_info"),
                "schema": self.schema,
            }
        )

        return MyBaseGraph(
            nodes=[
                fetch_node,
                parse_node,
                generate_answer_node,
            ],
            edges=[
                (fetch_node, parse_node),
                (parse_node, generate_answer_node)
            ],
            entry_point=fetch_node,
            graph_name=self.__class__.__name__
        )

    # def run(self) -> str:
    #     inputs = {"user_prompt": self.prompt, self.input_key: self.source}
    #     self.final_state, self.execution_info = self.graph.execute(inputs)
    #
    #     return self.final_state.get("answer", "No answer found.")
