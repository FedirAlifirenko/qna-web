import logging
from typing import Any, Generator, Iterable

import typer
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic.v1 import SecretStr

from qna_web import config
from qna_web.report import generate_report

logger = logging.getLogger(__name__)


def main(
    urls_filename: str,
    urls_chunk_size: int = 10,
    skip_report: bool = False,
) -> None:
    embeddings = OpenAIEmbeddings(
        api_key=SecretStr(config.OPENAI_API_KEY),
        model=config.OPENAI_EMBEDDINGS_MODEL_NAME,
    )

    urls = load_urls_from_file(urls_filename)

    html_documents = fetch_urls_as_docs(urls, urls_chunk_size=urls_chunk_size)
    split_html_documents = split_documents_and_save_index(html_documents, "html_vector_index", embeddings)

    transformer = Html2TextTransformer()
    text_documents = transformer.transform_documents(html_documents)
    split_documents_and_save_index(text_documents, "text_vector_index", embeddings)

    if not skip_report:
        generate_report(split_html_documents)


def split_documents_and_save_index(
    documents: Iterable[Document],
    vector_index_filename: str,
    embeddings: OpenAIEmbeddings,
) -> Iterable[Document]:
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name=config.OPENAI_MODEL_NAME,
        chunk_size=config.TEXT_SPLITTER_CHUNK_SIZE,
        chunk_overlap=config.TEXT_SPLITTER_CHUNK_OVERLAP,
    )
    split_documents = text_splitter.split_documents(documents)
    logger.info(f"Got {len(split_documents)} documents")

    vector = FAISS.from_documents(split_documents, embeddings)
    vector.save_local(vector_index_filename)
    logger.info(f"Saved index to {vector_index_filename}")
    return split_documents


def load_urls_from_file(filename: str) -> list[str]:
    with open(filename, "r") as f:
        urls = f.readlines()
    urls = [url.strip() for url in urls]
    logger.info(f"Loaded {len(urls)} urls from {filename}")
    return urls


def fetch_urls_as_docs(urls: list[str], urls_chunk_size: int = 10) -> list[Document]:
    loader = AsyncChromiumLoader([], headless=True)

    result_docs = []
    for urls_chunk in chunks(urls, urls_chunk_size):
        loader.urls = urls_chunk
        docs = loader.load()
        result_docs.extend(docs)

    logger.info(f"Loaded {len(result_docs)} documents from urls")
    return result_docs


def chunks(lst: list[Any], n: int) -> Generator[list[Any], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def entrypoint() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    typer.run(main)


if __name__ == "__main__":
    entrypoint()
