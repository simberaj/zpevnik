import sys, os
SONG_DEL = '\\beginsong{'
BAN_CHARS = '\\&/()'

def split(data, todir):
  songs = data.split(SONG_DEL)[1:]
  for song in songs:
    write(song, todir)

def write(song, todir):
  name = song.split('}', 1)[0]
  if 'by={' in song:
    author = ' - ' + song.split('by={', 1)[1].split('}]', 1)[0]
    for char in BAN_CHARS:
      if char in author:
        author = ''
        break
  else:
    author = ''
  fn = todir + '\\' + name + author + '.tex'
  with open(fn, 'w', encoding='utf8') as outfile:
    outfile.write(SONG_DEL + song)

if __name__ == '__main__':
  with open(sys.argv[1], encoding='utf8') as mainfile:
    todir = sys.argv[2]
    if not os.path.exists(todir):
      os.mkdir(todir)
    split(mainfile.read(), todir)