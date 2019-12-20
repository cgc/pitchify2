from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import json
import time

config = json.load(open('config.json'))
client_id = config.get('spotify_client_id')
client_secret = config.get('spotify_client_secret')

url = 'https://accounts.spotify.com/api/token'

def get_client():
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(token_url=url, client_id=client_id, client_secret=client_secret)
    return oauth

def album_search(client, artist, album, year=None):
    q=f'album:"{album}"'
    if artist:
        q += f' artist:"{artist}"'
    if year:
        q += f' year:"{year}"'
    return rate_limit_get(client, 'https://api.spotify.com/v1/search', params=dict(q=q, type='album'))

def rate_limit_get(client, *args, **kwargs):
    r = client.get(*args, **kwargs)
    if r.status_code == 429:
        print(f'Rate-limited. Sleeping {r.headers["retry-after"]}')
        # adding 1 for superstition based on https://stackoverflow.com/questions/30548073/spotify-web-api-rate-limits
        time.sleep(1+float(r.headers['retry-after']))
        return rate_limit_get(client, *args, **kwargs)
    r.raise_for_status()
    return r.json()

