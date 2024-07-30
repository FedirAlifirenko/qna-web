import logging
from typing import Any, Iterable

import pandas as pd
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import Runnable
from langchain_core.utils.function_calling import convert_to_openai_tool

from qna_web import config
from qna_web.dependencies import get_llm

logger = logging.getLogger(__name__)


class Vulnerability(BaseModel):
    name: str
    severity: str
    location: str
    description: str


class Answer(BaseModel):
    vulnerabilities: list[Vulnerability]


def generate_report(documents: Iterable[Document]) -> None:
    logger.info("Generating report")
    tags = ["input", "form", "script", "iframe", "object"]
    filtered_documents = [doc for doc in documents if any(tag in doc.page_content for tag in tags)]
    logger.info(f"Filtered {len(filtered_documents)} documents")

    llm_chain = _get_llm_chain()
    records = []
    for document in filtered_documents:
        logger.info(
            f"Processing document {document.metadata['source']}, content length: {len(document.page_content)}"
        )
        try:
            answer = llm_chain.invoke(
                {
                    "context": [document],
                    "input": "What critical security vulnerabilities can you identify in this HTML page? "
                    "Answer in the form of"
                    " name,"
                    " severity (LOW, MID or HIGH),"
                    " location (text pattern searchable in the html content),"
                    " and description.",
                }
            )
        except Exception as e:
            logging.error(f"Error processing document {document.metadata['source']}: {e}")
            continue

        for vulnerability in answer.vulnerabilities:
            records.append(
                {
                    "name": vulnerability.name,
                    "severity": vulnerability.severity,
                    "location": vulnerability.location,
                    "description": vulnerability.description,
                    "source": document.metadata["source"],
                }
            )

    df = pd.DataFrame.from_records(records)
    df.to_csv(config.REPORT_FILENAME, index=False)
    logger.info(f"Report saved to {config.REPORT_FILENAME}")


def _get_llm_chain() -> Runnable[dict[str, Any], Any]:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(
        """Answer the following question based only on the provided context:

        <context>
        {context}
        </context>

        Question: {input}
        """
    )
    tool_name = convert_to_openai_tool(Answer)["function"]["name"]
    structured_llm = llm.bind_tools([Answer], tool_choice=tool_name, parallel_tool_calls=False)
    output_parser = PydanticToolsParser(
        tools=[Answer],
        first_tool_only=True,
    )
    chain = create_stuff_documents_chain(structured_llm, prompt, output_parser=output_parser)
    return chain
