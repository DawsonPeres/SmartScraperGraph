# -*- coding: utf-8 -*-

"""
Custom AbstractGraph Module
"""

from abc import abstractmethod
from typing import Optional
from pydantic import BaseModel

from scrapegraphai.graphs import AbstractGraph


class MyAbstractGraph(AbstractGraph):

    def __init__(self, prompt: str, config: dict, source: Optional[str] = None, schema: Optional[BaseModel] = None):
        super().__init__(prompt, config, source, schema)

    @abstractmethod
    def _create_graph(self):
        """
        Abstract method to create a graph representation.
        """
        print("haha")
        pass
