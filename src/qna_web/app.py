import gradio as gr  # type: ignore[import-untyped]
import pandas as pd
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate

from qna_web import config
from qna_web.dependencies import get_embeddings, get_llm

llm = get_llm()
embeddings = get_embeddings()

html_vector = FAISS.load_local(
    config.HTML_VECTOR_INDEX_FILENAME, embeddings, allow_dangerous_deserialization=True
)
text_vector = FAISS.load_local(
    config.TEXT_VECTOR_INDEX_FILENAME, embeddings, allow_dangerous_deserialization=True
)

prompt = ChatPromptTemplate.from_template(
    """Answer the following question based on the provided history and context:
<history>
{history}
</history>

<context>
{context}
</context>

Question: {input}"""
)

document_chain = create_stuff_documents_chain(llm, prompt)
html_retrieval_chain = create_retrieval_chain(html_vector.as_retriever(), document_chain)
text_retrieval_chain = create_retrieval_chain(text_vector.as_retriever(), document_chain)


def chat_html_fn(message: str, history: list[tuple[str, str]]) -> str:
    response = html_retrieval_chain.invoke({"input": message, "history": _history_to_str(history)})
    return response["answer"]


def chat_text_fn(message: str, history: list[tuple[str, str]]) -> str:
    response = text_retrieval_chain.invoke({"input": message, "history": _history_to_str(history)})
    return response["answer"]


def _history_to_str(history: list[tuple[str, str]]) -> str:
    history_messages = []
    for user, assistant in history:
        history_messages.append(f"User: {user}")
        history_messages.append(f"Assistant: {assistant}")
        history_messages.append("\n")

    return "\n".join(history_messages)


def main() -> None:
    df = pd.read_csv(config.REPORT_FILENAME)

    with gr.Blocks(fill_width=True) as demo:
        with gr.Tabs():
            with gr.Tab("HTML"):
                gr.DataFrame(
                    df,
                    wrap=True,
                    column_widths=["10%", "10%", "30%", "30%", "20%"],
                    label="Possible vulnerabilities in the HTML pages",
                )

                gr.ChatInterface(fn=chat_html_fn, title="Q&A over html", chatbot=gr.Chatbot(scale=2))

            with gr.Tab("Text"):
                gr.ChatInterface(fn=chat_text_fn, title="Q&A over text", chatbot=gr.Chatbot(scale=2))

    demo.launch(auth=(config.APP_USER, config.APP_PASSWORD))


def entrypoint() -> None:
    main()


if __name__ == "__main__":
    entrypoint()
