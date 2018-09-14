import os
import os.path
import math
from tqdm import tqdm
from xml.etree import ElementTree

import requests


def download_page(href, id_):
    fdir = os.path.join("cache", str(id_)[-1])
    if not os.path.exists(fdir):
        os.mkdir(fdir)

    fname = os.path.join(fdir, "{}.xml".format(id_))
    if os.path.exists(fname):
        return

    r = requests.get("https://stockmarket.gov.ua/api/v1/{}".format(href))

    if r.status_code != 200:
        print("Cannot retrieve {}".format(href))
        return

    with open(fname, "w") as fp:
        fp.write(r.text)


def download_index():
    r = requests.get("https://stockmarket.gov.ua/api/v1/issuer-report-index.xml", params={"limit": 0})
    index = ElementTree.fromstring(r.content)
    num_pages = int(index.attrib["size"])
    id_min = int(index.attrib["id_min"])
    curr_id = int(index.attrib["id_max"])

    with tqdm(total=num_pages) as pbar:
        while curr_id > id_min:
            pg = requests.get("https://stockmarket.gov.ua/api/v1/issuer-report-index.xml", params={"idlast": curr_id})
            page = ElementTree.fromstring(pg.content)

            for item in page.findall(".//{http://stockmarket.gov.ua/api/v1/report-index.xsd}item"):
                href = item.attrib["href"]
                id_ = int(item.attrib["id"])

                download_page(href, id_)

                pbar.update(1)

                if id_ < curr_id:
                    curr_id = id_


if __name__ == '__main__':
    download_index()