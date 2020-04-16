import sys, os, locale, re, collections
locale.setlocale(locale.LC_ALL, '')

class Index:
  NUMERIC_KEY = '1-9'
  NAME_PATTERN = re.compile(r'(?<=\\beginsong\{).*?(?=\})')
  ARTIST_PATTERN = re.compile(r'(?<=\[by\=\{).*?(?=\}\])')
  SUBAUTHOR_SEPARATORS = [',', '/', 'feat.']

  def __init__(self, directory, extension='tex'):
    self.songlist = self.extractNames(self.loadFiles(directory, restrict=('.' + extension)))
    self.songlist.sort(key=lambda item: locale.strxfrm(item[0]))
  
  @staticmethod
  def loadFiles(directory, restrict=None):
    for fn in sorted(os.listdir(directory), key=locale.strxfrm):
      if restrict and restrict not in fn:
        continue # exclude all non-tex files
      with open(os.path.join(sys.argv[1], fn), encoding='utf8') as fin:
        yield fin.readline() # first line is where the title and artist is written
  
  @classmethod
  def extractNames(cls, lines):
    names = []
    for firstline in lines:
      nameMatch = cls.NAME_PATTERN.search(firstline)
      artistMatch = cls.ARTIST_PATTERN.search(firstline)
      if nameMatch is None:
        continue
      else:
        names.append((nameMatch.group(0), None if artistMatch is None else artistMatch.group(0)))
    return names
  
  @classmethod
  def groupByTitleStarts(cls, names):
    index = collections.defaultdict(list)
    # input: list of 2-tuples (title, artist)
    for i in range(len(names)):
      title = names[i][0]
      key = cls.getSortKey(title)
      index[key].append([title, None, i])
      if i != 0 and title == names[i-1][0]:
        index[key][-1][1] = names[i][1] # add artist discrimination
        index[key][-2][1] = names[i-1][1]
    for key in list(index.keys()):
      if not key.isalpha(): # group all titles starting with digits to one
        index[cls.NUMERIC_KEY].extend(index[key])
        del index[key]
    if cls.NUMERIC_KEY in index:
      index[cls.NUMERIC_KEY].sort()
    return index
  
  @classmethod
  def getSortKey(cls, title):
    if title[0].isalpha() and title.upper().startswith('CH'):
      return title[0:2]
    else:
      return title[0]
  
  @classmethod
  def groupByAuthors(cls, names):
    author_set = set(cls.correctAuthor(songdef[1]) for songdef in names if songdef[1])
    author_list = list(sorted(author_set, key=locale.strxfrm))
    index = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, item in enumerate(names):
      title, author = item
      if author:
        corrAuthor = cls.correctAuthor(author)
        index[cls.getSortKey(corrAuthor)][corrAuthor].append([title, None, i])
    return index
  
  @classmethod
  def correctAuthor(cls, author):
    for sep in cls.SUBAUTHOR_SEPARATORS:
      if sep in author:
        author = author[:author.find(sep)].rstrip()
    return author
  
  def titleTex(self):
    index = self.groupByTitleStarts(self.songlist)
    lines = []
    for key in sorted(index, key=locale.strxfrm):
      lines.append('\\begin{idxblock}{' + key + '}')
      for title, artist, i in index[key]:
        lines.append(self.entryTex(title, artist, i + 1))
      lines.append('\\end{idxblock}')
    return '\n'.join(lines)
  
  def authorTex(self):
    index = self.groupByAuthors(self.songlist)
    lines = []
    for key in sorted(index, key=locale.strxfrm):
      lines.append('\\begin{idxblock}{' + key + '}')
      for artist, entries in index[key].items():
        lines.append(self.headerTex(artist))
        for title, artist, i in entries:
          lines.append(self.entryTex(title, artist, i + 1))
      lines.append('\\end{idxblock}')
    return '\n'.join(lines)
  
  def headerTex(self, content):
    return '\\vspace{0.5ex}\\idxentry{\\textbf{%s}}{\\hspace{\\stretch{1}}}' % content
  
  def entryTex(self, title, artist=None, i=0):
    if artist is None:
      name = title
    else:
      name = title + ' \\emph{(' + artist + ')}'
    return '\\idxentry{%s}{\\hyperlink{song-%i}{\\pageref*{song-%i}}}' % (name, i, i)



def write(output, fpath):
  with open(fpath, 'w', encoding='utf8') as fileout:
    fileout.write(output)


if __name__ == '__main__':
  index = Index(sys.argv[1])
  write(index.titleTex(), sys.argv[2])
  write(index.authorTex(), sys.argv[3])
    