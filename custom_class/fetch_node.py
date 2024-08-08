# -*- coding: utf-8 -*-

""""
Custom FetchNode Module
"""

import json

import pandas as pd
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from scrapegraphai.nodes import FetchNode
from scrapegraphai.utils.cleanup_html import cleanup_html
from scrapegraphai.utils.convert_to_md import convert_to_md

from custom_class.chromium import MyChromiumLoader


class MyFetchNode(FetchNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, state):
        self.logger.info(f"--- Executing {self.node_name} Node ---")

        # Interpret input keys based on the provided input expression
        input_keys = self.get_input_keys(state)
        # Fetching data from the state based on the input keys
        input_data = [state[key] for key in input_keys]

        source = input_data[0]
        if (
                input_keys[0] == "json_dir"
                or input_keys[0] == "xml_dir"
                or input_keys[0] == "csv_dir"
                or input_keys[0] == "pdf_dir"
                or input_keys[0] == "md_dir"
        ):
            compressed_document = [
                source
            ]

            state.update({self.output[0]: compressed_document})
            return state
        # handling pdf
        elif input_keys[0] == "pdf":

            loader = PyPDFLoader(source)
            compressed_document = loader.load()
            state.update({self.output[0]: compressed_document})
            return state

        elif input_keys[0] == "csv":
            compressed_document = [
                Document(
                    page_content=str(pd.read_csv(source)), metadata={"source": "csv"}
                )
            ]
            state.update({self.output[0]: compressed_document})
            return state
        elif input_keys[0] == "json":
            f = open(source)
            compressed_document = [
                Document(page_content=str(json.load(f)), metadata={"source": "json"})
            ]
            state.update({self.output[0]: compressed_document})
            return state

        elif input_keys[0] == "xml":
            with open(source, "r", encoding="utf-8") as f:
                data = f.read()
            compressed_document = [
                Document(page_content=data, metadata={"source": "xml"})
            ]
            state.update({self.output[0]: compressed_document})
            return state
        elif input_keys[0] == "md":
            with open(source, "r", encoding="utf-8") as f:
                data = f.read()
            compressed_document = [
                Document(page_content=data, metadata={"source": "md"})
            ]
            state.update({self.output[0]: compressed_document})
            return state

        elif self.input == "pdf_dir":
            pass

        elif not source.startswith("http"):
            self.logger.info(f"--- (Fetching HTML from: {source}) ---")
            if not source.strip():
                raise ValueError("No HTML body content found in the local source.")

            if (not self.script_creator) or (self.force and not self.script_creator):
                parsed_content = convert_to_md(source)
            else:
                parsed_content = source

            compressed_document = [
                Document(page_content=parsed_content, metadata={"source": "local_dir"})
            ]

        elif self.use_soup:
            self.logger.info(f"--- (Fetching HTML from: {source}) ---")
            response = requests.get(source)
            if response.status_code == 200:
                if not response.text.strip():
                    raise ValueError("No HTML body content found in the response.")

                parsed_content = response

                if not self.cut:
                    parsed_content = cleanup_html(response, source)

                if (not self.script_creator) or (self.force and not self.script_creator):
                    parsed_content = convert_to_md(parsed_content, source)
                compressed_document = [Document(page_content=parsed_content)]
            else:
                self.logger.warning(
                    f"Failed to retrieve contents from the webpage at url: {source}"
                )

        else:
            self.logger.info(f"--- (Fetching HTML from: {source}) ---")
            loader_kwargs = {}

            if self.node_config is not None:
                loader_kwargs = self.node_config.get("loader_kwargs", {})

            loader = MyChromiumLoader([source], headless=self.headless, **loader_kwargs)
            document = loader.load()

            if not document or not document[0].page_content.strip():
                raise ValueError("No HTML body content found in the document fetched by ChromiumLoader.")
            parsed_content = document[0].page_content

            if (not self.script_creator) or (self.force and not self.script_creator and not self.openai_md_enabled):
                parsed_content = convert_to_md(document[0].page_content, source)

            compressed_document = [
                Document(page_content=parsed_content, metadata={"source": "html file"})
            ]

        state.update(
            {
                self.output[0]: compressed_document,
            }
        )

        return state
