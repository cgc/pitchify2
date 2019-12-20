python sync_pitchfork.py
python sync_spotify.py
ls data/pitchfork/*.json | cut -d '/' -f 3 | while read line; do python html_exporter.py $line; done
python html_exporter.py index
