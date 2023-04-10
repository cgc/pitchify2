import json
import jinja2
import os
import dateutil.parser
import datetime
import urllib.parse


def load_data(month_file):
    with open('data/spotify/'+month_file, 'r') as f:
        sp = dict([(tuple(k), v) for (k, v) in json.load(f)])
    with open('data/pitchfork/'+month_file, 'r') as f:
        pf = json.load(f)

    albums = []
    for a in pf:
        artists = [a['display_name'] for a in a['artists']]
        artist = artists[0] if artists else ''
        album = a['tombstone']['albums'][0]['album']['display_name']
        cover = a['tombstone']['albums'][0]['album']['photos']['tout']['sizes']['list']
        if sp.get((album, artist)):
            spotify = sp[album, artist]['uri']
        else:
            spotify = 'spotify:search:'+urllib.parse.quote(artist+' '+album)
        albums.append(dict(
            cover=cover,
            pitchfork='https://pitchfork.com'+a['url'],
            spotify=spotify,
            artist=artist,
            album=album,
        ))
    return albums


def export_mustache(month_file):
    albums = load_data(month_file)
    print(f'Generating page for {month_file}. {len(albums)} albums')

    with open('template.html', 'r') as f:
        template = f.read()

    out = template % json.dumps(albums)

    with open(f'reviews/{month_file[:-5]}.html', 'w') as f:
        f.write(out)


def export_jinja(month_file):
    albums = load_data(month_file)

    with open('template.html', 'r') as f:
        template = jinja2.Template(f.read())

    out = template.render(
        albums=albums,
    )
    with open(f'reviews/{month_file[:-5]}.html', 'w') as f:
        f.write(out)


def generate_index():
    ext = '.json'
    months = sorted([
        m[:-len(ext)]
        for m in os.listdir('data/pitchfork')
        if m.endswith(ext)
    ], reverse=True)

    with open('template_index.html', 'r') as f:
        template = jinja2.Template(f.read())
        with open(f'reviews/index.html', 'w') as html:
            html.write(template.render(months=months))

if __name__ == '__main__':
    import sys
    month = sys.argv[1]
    if month == 'index':
        generate_index()
    else:
        export_mustache(sys.argv[1])

