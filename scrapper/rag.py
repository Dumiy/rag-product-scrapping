from langchain_community.document_loaders.mongodb import MongodbLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate

# from langchain_community.embeddings import LlamaCppEmbeddings
from langchain_community.vectorstores import Chroma


import os
import shutil
import time

CHROMA_PATH = "./chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

KEY_WORD = """
You are an agent that extracts and classifies user input into product types furnitures:

{context}

---

Extract the key words to summary for data base usage like for example
2-Seater Hammock Bed Outdoor Chair Camping Hanging Hammocks Mesh
to
Outdoor Furniture

Solely classify in short words the input
"""


def query_data_response(question):

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    start = time.time()
    results = db.similarity_search_with_relevance_scores(question, k=3)
    if len(results) == 0 or results[0][1] < 0.1:
        print(len(results))
        print(results)
        return {"answer": "No results we're found regarding to this information"}
    print(f"Query find runtime {time.time()-start}")
    print(results)
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=question)

    del embeddings
    from langchain_community.llms import LlamaCpp
    from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path="./Llama-2-7B-Chat-GGUF/llama-2-7b-chat.Q8_0.gguf",
        callback_manager=callback_manager,
        verbose=True,  # Verbose is required to pass to the callback manager
    )

    output = llm.invoke(prompt)
    print(question)
    return {"answer": output}


def keyword_extract(sentence):

    from langchain_community.llms import LlamaCpp
    from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

    prompt_template = ChatPromptTemplate.from_template(KEY_WORD)
    prompt = prompt_template.format(context=sentence)
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path="./Llama-2-7B-Chat-GGUF/llama-2-7b-chat.Q8_0.gguf",
        callback_manager=callback_manager,
        verbose=True,  # Verbose is required to pass to the callback manager
    )

    output = llm.invoke(prompt)
    return {"answer": output}


def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)


def load_documents():
    loader = MongodbLoader(
        connection_string="mongodb://localhost:27017/",
        db_name="documents",
        collection_name="website",
        field_names=["url", "title", "code", "content", "document"],
    )
    documents = loader.load()
    return documents


def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=25,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    document = chunks[10]
    print(document.page_content)
    print(document.metadata)

    return chunks


def save_to_chroma(chunks: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    # llama = LlamaCppEmbeddings(model_path="./Llama-2-7B-Chat-GGUF/llama-2-7b-chat.Q8_0.gguf")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create a new DB from the documents.
    db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
