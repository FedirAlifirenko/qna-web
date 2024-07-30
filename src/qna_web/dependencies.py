from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic.v1 import SecretStr

from qna_web import config


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=SecretStr(config.OPENAI_API_KEY),
        model=config.OPENAI_MODEL_NAME,
        temperature=config.OPENAI_MODEL_TEMPERATURE,
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        api_key=SecretStr(config.OPENAI_API_KEY),
        model=config.OPENAI_EMBEDDINGS_MODEL_NAME,
    )
