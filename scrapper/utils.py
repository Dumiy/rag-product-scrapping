from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
from datetime import datetime
import re

CLEANR = re.compile("<.*?>")


def tag_visible(element: str):
    """
    Avoids javascript, css, metadata type text
    for extractions

    Args:
        element (str): html tags

    Returns:
        Content text
    """
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def findTitle(text: str):
    """
    Extract the title from bs4 content
    Args:
        text (str)

    Returns:
        Title
    """
    title = str(text).split("<title>")[1].split("</title>")[0]
    return title.replace("\\n", "").strip()


def text_from_html(body: str):
    """
    Extract all text type input and cleans
    extra newline and spaces

    Args:
        body (str): body for extraction (bs4)

    Returns:
        String with the website text content
    """
    soup = BeautifulSoup(body, "html.parser")
    headers = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    spans = soup.find_all("span")

    # Combine headers and spans into a single list
    elements = headers + spans

    # visible_texts = filter(tag_visible, elements)
    new_elem = []
    for t in elements:
        t = t.text
        text = re.sub(r"(\r\n){2,}", "\r\n", t.strip())
        if len(text) >= 2:
            new_elem.append(text)
    return "\n".join(t for t in new_elem)


def get_data_if_200(website: str):
    """
    Extract website content, cleans it
    normalize it then returns in JSON format

    Args:
        website (str): URL

    Returns:
        dict:
            url: website called
            code: status code for GET
            time: time of the operation
            title: Title extracted from site
            content: Text content for website
        code: Int
    """
    try:
        html = urllib.request.urlopen(website)
        response_code = html.getcode()
        if response_code == 200:
            html = html.read()
            title = findTitle(html)
            text = text_from_html(html)
            text = "\n".join(
                text_from_html(html).split("\n")
            )  # Reduce redundant set maybe
            print(text)
            entry = {
                "url": website,
                "code": response_code,
                "time": datetime.now(),
                "title": title,
                "content": text,
                "document": "",
            }
            return entry, response_code
    except urllib.error.HTTPError as e:
        print(e)
    if "response_code" in locals():
        entry = {
            "url": website,
            "code": response_code,
            "time": datetime.now(),
            "title": title,
            "content": "",
        }
    else:
        response_code = 404
        entry = {"content": ""}
    return entry, response_code


def run_scraping(entry, page_handle):

    website = f"{page_handle}{entry['handle']}"
    data, response_code = get_data_if_200(website)
    text = data["content"]

    document = f"""
    Title : {entry['title']}
    Tags: {entry['tags']}
    Product type: {entry['product_type']}
    Description: {re.sub(CLEANR, '', entry['body_html'])}
    Content : {text}
    """
    data_entry = {
        "url": website,
        "code": response_code,
        "time": datetime.now(),
        "title": entry["title"],
        "content": "",
        "document": document,
    }
    return data_entry
