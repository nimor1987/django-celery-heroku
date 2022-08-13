from django.shortcuts import render
from ticker.models import WSBPosts
import datetime
import yfinance as yf
import pandas as pd
from plotly.offline import plot
import plotly.express as px


def index(request):

    query = WSBPosts.objects.all().values()

    post_data = pd.DataFrame.from_records(query)
    top_ticker = [
        ticker
        for ticker in post_data["ticker"]
        .groupby(post_data["ticker"])
        .count()
        .sort_values(ascending=False)[:3]
        .index
    ]
    most_mentioned = (
        post_data["ticker"]
        .groupby([post_data["ticker"], post_data["created"].dt.date])
        .count()
        .sort_values(ascending=False)[0]
    )
    numdays = 14
    base = datetime.date.today()
    date_list = [base - datetime.timedelta(days=x) for x in range(numdays)]
    date_df = pd.DataFrame(date_list, columns=["created"])

    wsb_plots = []
    for ticker in top_ticker:
        counts = (
            post_data[post_data["ticker"] == ticker]["ticker"]
            .groupby([post_data["created"].dt.date])
            .count()
        )
        plot_df = date_df.merge(counts.reset_index(), how="left").fillna(0)
        fig = px.bar(
            plot_df,
            x="created",
            y="ticker",
            labels={"created": "Date", "ticker": "Mentions"},
            width=740,
            height=385,
        )
        fig.update_xaxes(tickmode="linear")
        fig.update_layout(yaxis_range=[0, most_mentioned + 2])
        plot_div = plot(fig, output_type="div")
        wsb_plots.append(plot_div)

    yf_plots = []
    for ticker in top_ticker:
        yf_tkr = yf.Ticker(ticker)
        start = datetime.date.today() - datetime.timedelta(days=14)
        hist = yf_tkr.history(start=start, interval="1h")
        hist.index = hist.index.set_names(["Date"])
        fig = px.line(
            hist,
            y="Close",
            labels={"index": "Date", "Close": "Price"},
            width=740,
            height=385,
        )
        fig.update_xaxes(tickmode="linear")
        plot_div = plot(fig, output_type="div")
        yf_plots.append(plot_div)

    popular_posts = []
    for ticker in top_ticker:
        posts = []
        for _, row in (
            post_data[post_data["ticker"] == ticker]
            .sort_values("score", ascending=False)[:3]
            .iterrows()
        ):
            posts.append(
                {
                    "title": row["title"],
                    "score": row["score"],
                    "link": row["link"],
                    "created": row["created"],
                }
            )
        popular_posts.append(posts)

    data = zip(wsb_plots, yf_plots, popular_posts, top_ticker)
    context = {"data": data}

    return render(request, "index.html", context)
