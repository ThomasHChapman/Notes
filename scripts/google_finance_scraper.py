# Credit to u/zdmit @ reddit for this script.


import requests, json, re
from parsel import Selector


def scrape_google_finance_main_page():
    # https://docs.python-requests.org/en/master/user/quickstart/#custom-headers
    # https://www.whatismybrowser.com/detect/what-is-my-user-agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36"
        }

    html = requests.get(f"https://www.google.com/finance/", headers=headers, timeout=30)
    selector = Selector(text=html.text)
    
    # where all extracted data will be temporary located
    ticker_data = {
        "market_trends": [],
        "interested_in": {
            "top_position": [],
            "bottom_position": []
        },
        "earning_calendar": [],
        "most_followed_on_google": [],
        "news": [],
    }

    # Market trends top results
    ticker_data["market_trends"] = selector.css(".gR2U6::text").getall()
    
    # Earnings calendar results
    for calendar_quote in selector.css(".d3fRjc"):
        ticker_data["earning_calendar"].append({
            "quote": calendar_quote.css(".yaubCc::text").get(),
            "quote_link": f'https://www.google.com/finance/quote{calendar_quote.css(".yaubCc::attr(href)").get().replace("./quote/", "/")}',
            "short_date": calendar_quote.css(".JiAI5b").xpath("normalize-space()").get(),
            "full_date": calendar_quote.css(".fVovwd::text").get()
        })

    # Most followed on Google results
    for google_most_followed in selector.css(".NaLFgc"):
        current_percent_change_raw_value = google_most_followed.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"by\s?(\d+\.\d+)%", google_most_followed.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group(1)

        ticker_data["most_followed_on_google"].append({
            "title": google_most_followed.css(".TwnKPb::text").get(),
            "quote": re.search(r"\.\/quote\/(\w+):",google_most_followed.attrib["href"]).group(1),            # https://regex101.com/r/J3DDIX/1
            "following": re.search(r"(\d+\.\d+)M", google_most_followed.css(".Iap8Fc::text").get()).group(1), # https://regex101.com/r/7ptVha/1
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    # news results. If empty -> run once again. For some reason it could return [].
    for index, news in enumerate(selector.css(".yY3Lee"), start=1):
        ticker_data["news"].append({
            "position": index,
            "title": news.css(".Yfwt5::text").get(),
            "link": news.css(".z4rs2b a::attr(href)").get(),
            "source": news.css(".sfyJob::text").get(),
            "published": news.css(".Adak::text").get(),
            "thumbnail": news.css("img.Z4idke::attr(src)").get()
        })

    # "you may be interested in" at the top of the page results
    for index, interested_top in enumerate(selector.css(".sbnBtf:not(.xJvDsc) .SxcTic"), start=1):
        current_percent_change_raw_value = interested_top.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%", interested_top.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        ticker_data["interested_in"]["top_position"].append({
            "index": index,
            "title": interested_top.css(".ZvmM7::text").get(),
            "quote": interested_top.css(".COaKTb::text").get(),
            "price_change": interested_top.css(".SEGxAb .P2Luy::text").get(),
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    # "you may be interested in" at the bottom of the page results
    for index, interested_bottom in enumerate(selector.css(".HDXgAf .tOzDHb"), start=1):
        # single function to handle both top and bottom 
        # "you may be interested results" as selectors is identical

        current_percent_change_raw_value = interested_bottom.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%", interested_bottom.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        ticker_data["interested_in"]["bottom_position"].append({
            "position": index,
            "ticker": interested_bottom.css(".COaKTb::text").get(),
            "ticker_link": f'https://www.google.com/finance{interested_bottom.attrib["href"].replace("./", "/")}',
            "title": interested_bottom.css(".RwFyvf::text").get(),
            "price": interested_bottom.css(".YMlKec::text").get(),
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    return ticker_data


print(json.dumps(scrape_google_finance_main_page(), indent=2, ensure_ascii=False))
Outputs:

{
  "market_trends": {
    "top_position": [
      "Market indexes",
      "Most active",
      "Gainers",
      "Losers",
      "Climate leaders",
      "Crypto",
      "Currencies"
    ],
    "bottom_position": [
      {
        "index": 1,
        "title": "Tesla Inc",
        "quote": "TSLA",
        "price": "$824.46",
        "price_percent_change": "+0.59%"
      }, ... other results
      {
        "index": 6,
        "title": "BEL 20",
        "quote": "Index",
        "price": "3,774.05",
        "price_percent_change": "+1.15%"
      }
    ]
  },
  "interested_in": {
    "top_position": [
      {
        "index": 1,
        "title": "Tesla Inc",
        "quote": "TSLA",
        "price_change": "+$47.88",
        "percent_price_change": "+6.17%"
      }, ... other results
      {
        "index": 6,
        "title": "BEL 20",
        "quote": "Index",
        "price_change": "+22.01",
        "percent_price_change": "+0.59%"
      }
    ],
    "bottom_position": [
      {
        "position": 1,
        "ticker": "Index",
        "ticker_link": "https://www.google.com/finance/quote/BEL20:INDEXEURO",
        "title": "BEL 20",
        "price": "3,774.05",
        "percent_price_change": "+0.59%"
      }, ... other results
      {
        "position": 18,
        "ticker": "PFE",
        "ticker_link": "https://www.google.com/finance/quote/PFE:NYSE",
        "title": "Pfizer Inc.",
        "price": "$51.95",
        "percent_price_change": "-0.67%"
      }
    ]
  },
  "earning_calendar": [
    {
      "quote": "Apple",
      "quote_link": "https://www.google.com/finance/quote/AAPL:NASDAQ",
      "short_date": "Jul28",
      "full_date": "Jul 28, 2022, 11:00 PM"
    }, ... other results
    {
      "quote": "Occidental Petroleum",
      "quote_link": "https://www.google.com/finance/quote/OXY:NYSE",
      "short_date": "Aug2",
      "full_date": "Aug 2, 2022, 10:00 PM"
    }
  ],
  "most_followed_on_google": [
    {
      "title": "Apple Inc",
      "quote": "AAPL",
      "following": "3.71",
      "percent_price_change": "+3.42"
    }, ... other results
    {
      "title": "Tesla Inc",
      "quote": "TSLA",
      "following": "1.49",
      "percent_price_change": "+6.17"
    }
  ],
  "news": [
    {
      "position": 1,
      "title": "This kind of shock to the economy will have consequences",
      "link": "https://www.cnn.com/2022/07/27/politics/fed-interest-rate-volcker-what-matters/index.html",
      "source": "CNN",
      "published": "10 hours ago",
      "thumbnail": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRcLNm7uU5YfuvveVMWNvlQGUMcCPi4-7QJAqfKcDJgq7A3n1E_wiy53--_FFA"
    }, ... other news
    {
      "position": 9,
      "title": "The 20 Best Netflix Shows of All Time -- Ranked",
      "link": "https://www.rollingstone.com/tv-movies/tv-movie-lists/best-netflix-shows-1386323/",
      "source": "Rolling Stone",
      "published": "20 hours ago",
      "thumbnail": "https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcSsaABpxAxYW29MTnyeSHb1Z9ex1bMvXQQnFB5RJqz9LogWOR9zyOKw9YrjClI"
    }
  ]
}