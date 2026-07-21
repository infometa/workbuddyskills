import hashlib
import hmac
import json
import time
import os
from datetime import datetime, timedelta, timezone

from dataclasses import dataclass
from http.client import HTTPSConnection
import argparse
from typing import List

HOST = "api.wsa.cloud.tencent.com"

@dataclass
class Doc:
    url : str
    title: str
    snippet: str
    date: str
    site: str
    images: List[str]

@dataclass
class Option:
    query:str
    mode: int
    site:str
    from_time:int
    to_time:int

def generate_header_and_payload(params:Option, secret_key:str):
    # ************* 构造header *************
    headers = {
        "Authorization": "Bearer " + secret_key,
        "Content-Type": "application/json; charset=utf-8",
        "Host": HOST
    }

    # ************* 构造payload *************
    body = {"Query": params.query, "Mode":params.mode}
    if len(params.site) > 0:
        body["Site"] = params.site
    if params.from_time > 0 and params.to_time > 0:
        body["FromTime"] = params.from_time
        body["ToTime"] = params.to_time
    payload = json.dumps(body)

    return headers, payload


# api-key可前往官网控制台 https://console.cloud.tencent.com/wsapi/index 进行获取

def search(params:Option, secret_key:str):
    headers,payload = generate_header_and_payload(params, secret_key=secret_key)
    query = params.query
    try:
        req = HTTPSConnection(HOST)
        req.request("POST", "/SearchPro", headers=headers, body=payload.encode("utf-8"))
        resp = req.getresponse()
        rsp = resp.read()
        ret = json.loads(rsp)
        docs, error_msg = parse(ret)
        if error_msg:
            print(f"## 搜索失败\n原因:{error_msg}")
            return
        print(f"## 查询词:{query}, 搜索结果:{len(docs)}条")
        for idx, doc in enumerate(docs):
            line = (
                f"{idx + 1}. [{doc.title}]({doc.url})\n"
                f"    - 摘要: {doc.snippet}\n"
                f"    - 内容发布时间: {doc.date}\n"
                f"    - 网站: {doc.site}"
            )
            if doc.images and len(doc.images) > 0:
                images_info = "\t".join(doc.images)
                print(line + f"\n    - 相关图片: {images_info}")
            else:
                print(line)
    except Exception as err:
        print(f"request error: {err}")

def parse(rsp:dict):
    error_msg = ""
    res = rsp.get("Response")
    if res is None or not isinstance(res, dict):
        print("response is null")
        return [], error_msg
    
    error = res.get("Error")
    if error is not None:
        error_msg = error.get("Message", "")
        return [], error_msg

    pages = res.get("Pages")
    if pages is None:
        return [], error_msg

    docs = []
    for page in pages:
        json_page = json.loads(page)
        is_vr = json_page.get("vr", False)
        if is_vr:
            display = json_page.pop("display", None)
            if display is None:
                continue
            url = display.get("url")
            title = display.get("title")
            date = display.get("date")
            content = page
            docs.append(Doc(url=url, title=title, site="", date=date, snippet=content, images=[]))
        else:
            passage = json_page.get("passage")
            url = json_page.get("url")
            title = json_page.get("title")
            site = json_page.get("site")
            date = json_page.get("date")
            if len(title) == 0 or len(passage) == 0:
                continue
            docs.append(Doc(url = url,title= title, site=site, date=date, snippet=passage, images=json_page.get("images")))
    return docs, error_msg


if __name__=="__main__":
    api_key =  os.getenv("TENCENTCLOUD_WSA_APIKEY")

    if api_key is None:
        print("api-key are not set, 前往 https://console.cloud.tencent.com/wsapi/index 进行获取")
        exit(1)

    parser = argparse.ArgumentParser(description="websearch command arguments")
    parser.add_argument("--query", type=str, help="search query", required=True)
    parser.add_argument("--mode", type=int, help="返回结果类型，0-自然检索结果(默认)，1-多模态VR结果，2-混合结果（多模态VR结果+自然检索结果)", default=0)
    parser.add_argument("--site",type=str, help="指定站点搜索", default="")
    parser.add_argument("--freshness", choices=['','day','week','month','year'], help="查询结果的时效性要求")

    args = parser.parse_args()
    if len(args.query) == 0:
        print("invalid input arguments, query is empty")
        exit(1)

    reqOptions = Option(
        query=args.query,
        mode=args.mode,
        site=args.site,
        from_time=-1,
        to_time=-1
    )
    current_time = datetime.now()
    start_date = None
    if args.freshness == 'day':
        start_date = (current_time - timedelta(days=1))
    elif args.freshness == 'week':
        start_date = (current_time - timedelta(weeks=1))
    elif args.freshness == 'month':
        start_date = (current_time - timedelta(days=30))
    elif args.freshness == 'year':
        start_date = (current_time - timedelta(days=365))

    if start_date is not None:
        reqOptions.from_time = int(start_date.timestamp())
        reqOptions.to_time = int(current_time.timestamp())

    search(reqOptions, api_key)
