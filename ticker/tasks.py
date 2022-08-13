from celery import shared_task
import collections
import re
import requests
import datetime
import pandas as pd
from ticker.login import USERNAME, PASSWORD, CLIENT_ID, CLIENT_SECRET
from django.utils.timezone import make_aware
from ticker.models import WSBPosts


def tickers_from_title(title):

    tickers = [
        re.search(r"[A-Z]+", word).group()
        for word in title.strip(".?!").split()
        if word.isupper()
        and (2 <= len(word) <= 4 or word.startswith("$") or word.endswith("$"))
    ]

    return tickers


def ticker_dist(reddit_data):

    common_not_stocks = [
        "YOLO",
        "GAIN",
        "LOSS",
        "PORN",
        "IS",
        "OR",
        "WSB",
        "DD",
        "EOW",
        "EOM",
        "EOY",
        "IRL",
        "IDK",
    ]
    ticker_dist = []
    for post in reddit_data.json()["data"]["children"]:
        title = post["data"]["title"]
        tickers = tickers_from_title(title)
        if tickers:
            for ticker in tickers:
                if ticker not in common_not_stocks:
                    ticker_dist.append(ticker)
    ticker_dist_top = []
    for ticker in collections.Counter(ticker_dist).most_common(10):
        ticker_dist_top.append(ticker[0])

    return ticker_dist_top


def fetch_wsb_posts(USERNAME, PASSWORD, CLIENT_ID, CLIENT_SECRET):

    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "password", "username": USERNAME, "password": PASSWORD}
    headers = {"User-Agent": "wsb-ticker"}
    token_access_endpoint = "https://www.reddit.com/api/v1/access_token"
    res = requests.post(token_access_endpoint, auth=auth, data=data, headers=headers)
    token = res.json()["access_token"]
    headers = {**headers, **{"Authorization": f"bearer {token}"}}
    endpoint = "https://oauth.reddit.com"
    wsb_new = requests.get(
        endpoint + "/r/wallstreetbets/new", headers=headers, params={"limit": 100}
    )

    return wsb_new


@shared_task(bind=True)
def wsb_scrape(self):

    wsb_new = fetch_wsb_posts(USERNAME, PASSWORD, CLIENT_ID, CLIENT_SECRET)
    top_tickers = ticker_dist(wsb_new)
    post_datas = []
    for post in wsb_new.json()["data"]["children"]:
        title = post["data"]["title"]
        tickers = tickers_from_title(title)
        if tickers:
            for ticker in tickers:
                if ticker in top_tickers:
                    post_data = {
                        "ticker": ticker,
                        "name": post["data"]["name"],
                        "title": post["data"]["title"],
                        "score": post["data"]["score"],
                        "link": post["data"]["permalink"],
                        "created": make_aware(
                            datetime.datetime.fromtimestamp(post["data"]["created_utc"])
                        ),
                    }
                    post_datas.append(post_data)
                    obj, created = WSBPosts.objects.update_or_create(
                        ticker=post_data["ticker"],
                        name=post_data["name"],
                        defaults=post_data,
                    )
