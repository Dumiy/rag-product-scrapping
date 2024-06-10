from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
import re


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(string=True)
    visible_texts = filter(tag_visible, texts)
    new_elem = []
    for t in visible_texts:
        text = re.sub(r'(\r\n){2,}','\r\n', t.strip())
        if len(text) >=2:
            new_elem.append(text)
    return "\n".join(t for t in new_elem)

html = urllib.request.urlopen('https://www.factorybuys.com.au/products/double-swing-hammock-bed-cream').read()
print(len("\n".join(set(text_from_html(html).split("\n"))).encode("utf-8")))
