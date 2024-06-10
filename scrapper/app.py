from typing import Union
from datetime import datetime

import concurrent.futures
import asyncio
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm

import csv
import codecs


import pymongo
from fastapi import FastAPI, File, UploadFile

from utils import get_data_if_200, run_scraping
from rag import generate_data_store, query_data_response

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/test_llama")
def test_llama():
    from langchain_community.llms import LlamaCpp
    from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
    from langchain_core.prompts import PromptTemplate

    template = """Question: {question}

    Answer: Let's work this out in a step by step way to be sure we have the right answer."""

    prompt = PromptTemplate.from_template(template)
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path="/scrapper/model/llama-2-7b-chat.Q8_0.gguf",
        temperature=0.75,
        max_tokens=2000,
        top_p=1,
        callback_manager=callback_manager,
        verbose=True,  # Verbose is required to pass to the callback manager
    )
    question = """
    Question: A rap battle between Stephen Colbert and John Oliver
    """
    output = llm.invoke(question)
    return {"Success": output}


@app.get("/llama/gen_docs")
def gen_emb_store():
    generate_data_store()
    return {"Sucess"}


@app.post("/llama/question")
def call_with_question(question: str):
    return query_data_response(question)


@app.post("/website/url")
async def create_entry(website: str):
    """

    Adds entry into mongodb with url link
    With all html text from page
    Return status or if already present

    Args:
        website (str): _description_

    Returns:
        {
            url: str
            status: str/int (Success or Code)
        }
    """
    myclient = pymongo.MongoClient("mongodb://veridion-pt2-mongodb-1:27017/")
    documents = myclient["documents"]
    website_collection = documents["website"]
    present = list(website_collection.find({"url": website}))

    if len(present) > 0:
        return {"status": "Already present"}

    entry, code = get_data_if_200(website)
    if code == 200:
        website_collection.insert_one(entry)
        myclient.close()
        return {"status": "Success"}

    myclient.close()
    return {"url": website, "status": code}


@app.post("/website/csv")
async def create_documents(
    file: UploadFile = File(...),
    page_handle: str = "https://www.factorybuys.com.au/products/",
):

    csvReader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))
    myclient = pymongo.MongoClient("mongodb://veridion-pt2-mongodb-1:27017/")
    documents = myclient["documents"]
    website_collection = documents["website"]
    data = []
    for rows in csvReader:
        present = list(website_collection.find({"title": rows["title"]}))
        if len(present) > 0:
            continue
        data.append(rows)
    file.file.close()
    if len(data) == 0:
        return {"Status": "Not executed", "Reason": "Files already in DB"}

    idx = 0
    for data_point in tqdm(data):
        data_point = run_scraping(data_point, page_handle)
        website_collection.insert_one(data_point)
        idx += 1
    # results = await run_scraping_async(data, page_handle)

    # for item in results:

    #     website_collection.insert_one(item)
    myclient.close()

    return {"Status": "Success", "Files writen in DB:": idx}


async def run_scraping_async(entries, page_handle):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        tasks = [
            loop.run_in_executor(pool, run_scraping, entry, page_handle)
            for entry in entries
        ]
        # Use tqdm to create a progress bar
        results = []
        for f in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Processing"):
            result = await f
            results.append(result)

        return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)
