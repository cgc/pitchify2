import os
from glob import glob
import spotify_client
import json
import re


def _strip_ep_ost(album):
    '''
    >>> _strip_ep_ost('Hi EP')=='Hi'
    >>> _strip_ep_ost('Hi OST')=='Hi'
    >>> _strip_ep_ost('Hi LP')=='Hi'
    >>> _strip_ep_ost('Hi LP ')=='Hi LP '
    '''
    album = re.sub(r' EP$', '', album, flags=re.IGNORECASE)
    album = re.sub(r' LP$', '', album, flags=re.IGNORECASE)
    album = re.sub(r' OST$', '', album, flags=re.IGNORECASE)
    return album

def strip_punctuation(string):
    '''
    This function drops punctuation, while carefully dropping words that contain a quote.
    >>> assert strip_punctuation('I Ain’t Marching Anymore') == 'I Marching Anymore'
    >>> assert strip_punctuation('Twin Peaks: Fire Walk With Me') == 'Twin Peaks Fire Walk With Me'
    '''
    return ' '.join([
        w
        for w in re.split(r"[^'’\w]", string)
        if w and "'" not in w and '’' not in w
    ])


def hacky_album_search(client, artist, album, year):
    items = spotify_client.album_search(client, artist, album, year=year)['albums']['items']
    if items: return items
    # Now try without EP/OST/etc
    items = spotify_client.album_search(client, artist, _strip_ep_ost(album), year=year)['albums']['items']
    if items: return items
    # Now try without year
    items = spotify_client.album_search(client, artist, _strip_ep_ost(album))['albums']['items']
    if items: return items
    # Now try by removing punctuation from album & artist and return what we get
    items = spotify_client.album_search(
        client,
        strip_punctuation(artist),
        strip_punctuation(_strip_ep_ost(album))
    )['albums']['items']
    return items



def outdated_spotify(month_file):
    if os.path.exists('data/spotify/'+month_file):
        pf = os.stat('data/pitchfork/'+month_file).st_mtime
        sp = os.stat('data/spotify/'+month_file).st_mtime
        return sp < pf
    else:
        return True


def log_items(items):
    for a in items:
        aa = ', '.join(art['name'] for art in a['artists'])
        print(f"type={a['type']} album_type={a.get('album_type')} release_date={a['release_date']} name={a['name']} artists={aa}")


def update_spotify(client, month_file):
    with open('data/pitchfork/'+month_file, 'r') as f:
        pf = json.load(f)

    # Now load any existing data
    loaded = {}
    spotify_file = 'data/spotify/'+month_file
    if os.path.exists(spotify_file):
        with open(spotify_file, 'r') as f:
            loaded = dict([
                (tuple(k), v) for (k, v) in json.load(f)])

    # Now iterate over pitchfork entries & run searches for any missing data.
    for a in pf:
        album = a['tombstone']['albums'][0]['album']['display_name']
        year = a['tombstone']['albums'][0]['album']['release_year']
        artist = a['artists'][0]['display_name'] if a['artists'] else ''
        if (album, artist) in loaded:
            continue
        print('searching for ', artist, album, year)
        items = hacky_album_search(client, artist, album, year)
        if items:
            if len(items)>1:
                print(f'Warning, found more than one item for artist:{artist}, album:{album}')
                try:
                    log_items(items)
                except:
                    pass
            loaded[album, artist] = items[0]
        else:
            print('No results')

    # Now write out loaded data
    with open(spotify_file, 'w') as f:
        json.dump(list(loaded.items()), f)


def sync():
    client = spotify_client.get_client()
    files = sorted(os.listdir('data/pitchfork'))
    for f in files:
        if outdated_spotify(f):
            print('Updating', f)
            update_spotify(client, f)


if __name__ == '__main__':
    sync()
