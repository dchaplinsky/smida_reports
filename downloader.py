import os
import os.path
import math
import json
import xmltodict
from tqdm import tqdm
from xml.etree import ElementTree

import requests


def convert_params(doc):
    if isinstance(doc, dict):
        new_doc = {}

        for d in doc:
            new_k = d.lstrip("@")
            if d == "param" and isinstance(doc[d], (list, tuple)):
                new_doc[new_k] = {
                    node["@name"]: node.get("#text") for node in doc[d]
                }
            else:
                new_doc[new_k] = convert_params(doc[d])

        doc = new_doc
    elif isinstance(doc, (list, tuple)):
        doc = [
            convert_params(d) for d in doc
        ]

    return doc

def download_page(href, id_):
    fdir = os.path.join("cache", str(id_)[-1])
    if not os.path.exists(fdir):
        os.mkdir(fdir)

    fname = os.path.join(fdir, "{}.xml".format(id_))
    if os.path.exists(fname):
        with open(fname, "r") as fp:
            s = fp.read()
            if s:
                return xmltodict.parse(s)
            else:
                print("Cached response for {} is empty".format(href))

    r = requests.get("https://stockmarket.gov.ua/api/v1/{}".format(href))

    if r.status_code != 200:
        print("Cannot retrieve {}".format(href))
        return

    with open(fname, "w") as fp:
        fp.write(r.text)

    return xmltodict.parse(r.text)


def download_index():
    r = requests.get("https://stockmarket.gov.ua/api/v1/issuer-report-index.xml", params={"limit": 0})
    index = ElementTree.fromstring(r.content)
    num_pages = int(index.attrib["size"])
    id_min = int(index.attrib["id_min"])
    curr_id = int(index.attrib["id_max"])

    with open("out.jsonlines", "w") as fp:
        with tqdm(total=num_pages) as pbar:
            while curr_id > id_min:
                pg = requests.get("https://stockmarket.gov.ua/api/v1/issuer-report-index.xml", params={"idlast": curr_id})
                page = ElementTree.fromstring(pg.content)

                for item in page.findall(".//{http://stockmarket.gov.ua/api/v1/report-index.xsd}item"):
                    href = item.attrib["href"]
                    id_ = int(item.attrib["id"])

                    res = convert_params(download_page(href, id_))
                    if res is not None:
                        fp.write(json.dumps(res, ensure_ascii=False) + "\n")

                    pbar.update(1)

                    if id_ < curr_id:
                        curr_id = id_


if __name__ == '__main__':
    download_index()
