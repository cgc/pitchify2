import os
import requests
import json
import dateutil.parser as parser
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# from https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

browser = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'

markerfile = 'data/pitchfork-last-download-pubDate'

def gen_reviews(size=12):
    idx = 0
    while True:
        r = http.get('https://pitchfork.com/api/v2/search/', params=dict(
            types='reviews',
            hierarchy='sections/reviews/albums,channels/reviews/albums',
            sort='publishdate desc,position asc',
            size=size,
            start=idx*size,
        ), headers={
            'User-Agent': browser,
            'Accept': 'application/json',
            'Referer': 'https://pitchfork.com/reviews/albums/',
        })
        results = r.json()['results']['list']
        print(f'Loaded page {idx} with {len(results)} results.')
        if not results:
            return
        yield from results
        idx += 1

def _date_to_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def _date_to_month_string(dt):
    return dt.date().isoformat()[:-3]

def sync():
    # Figure out how far back we have to sync. We include the entire month
    # of the last synced pub.
    if os.path.exists(markerfile):
        with open(markerfile, 'r') as f:
            last_pubDate = f.read()
    else:
        # HACK the limit of how far back we go...
        last_pubDate = '2017-01-01T00:00:00+00:00'
    last_month = _date_to_month(parser.parse(last_pubDate))

    next_marker = None

    # Gather reviews by month.
    reviews = {}
    for r in gen_reviews():
        dt = parser.parse(r['pubDate'])
        # Stop going through reviews once we get too far back
        if dt < last_month:
            break
        reviews.setdefault(_date_to_month_string(dt), []).append(r)

        # Store first review we see...
        if next_marker is None:
            next_marker = r['pubDate']

    # Write reviews to disk, by month.
    for month, rs in reviews.items():
        with open(f'data/pitchfork/{month}.json', 'w') as f:
            json.dump(rs, f)

    # Write marker to disk.
    with open(markerfile, 'w') as f:
        f.write(next_marker)

if __name__ == '__main__':
    sync()
