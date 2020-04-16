import sys, os, locale, re
locale.setlocale(locale.LC_ALL, '')

TITLE_RE = re.compile(r'(?<=\\beginsong\{)\w+(?=\})')
ARTIST_RE = re.compile(r'(?<=\[by\=\{).+?(?=\}\])')

SONG_SORTER = lambda tup: locale.strxfrm(tup[0]) + locale.strxfrm(tup[1])

if __name__ == '__main__':
  infolder = sys.argv[1]
  outname = sys.argv[2] if len(sys.argv) > 2 else 'index.tex'
  items = []
  # load all titles and artists
  for fn in os.listdir(infolder):
    if '.tex' not in fn: continue
      with open(os.path.join(sys.argv[1], fn), encoding='utf8') as fin:
        title = None
        artist = None
        for line in fin:
          if not title:
            titlepat = TITLE_RE.search(line)
            if titlepat: title = titlepat.group(0)
          if not artist:
            artpat = ARTIST_RE.search(line)
            if artpat: artist = artpat.group(0)
          if title and artist:
            items.append(title, artist)
            break
  # sort'em
  items.sort(key=SONG_SORTER)
  # write it out
  with open(outname, 'w', encoding='utf8') as fout:
