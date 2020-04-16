import sys, os, locale, collections, json
import statistics
locale.setlocale(locale.LC_ALL, '')

# pridavani akordu k dalsimu slovu - aby nebyly mezery
# jak to vypada s vicenasobnymi registry akordu na zacatku?


class Song:
  PLAIN_DESC_PREFIX = ' ' * 5

  def __init__(self):
    self.desc = []
    self.verses = []
    self.chords = set()
    self.artist = None
  
  def readFile(self, fileName):
    try:
      with open(fileName, encoding='utf8') as file:
        return file.readlines()
    except UnicodeDecodeError:
      with open(fileName, encoding='cp1250') as file:
        return file.readlines()  
  
  def readPlain(self, fileName):
    lines = self.readFile(fileName)
    line = self.skipWhiteLines(lines, 0)
    line = self.loadPlainHeader(lines, line)
    line = self.skipWhiteLines(lines, line)
    line = self.loadPlainDescription(lines, line)
    self.loadPlainText(lines, line)
  
  def skipWhiteLines(self, lines, start):
    line = start
    while line < len(lines) and not lines[line].strip():
      line += 1
    return line
  
  def loadPlainHeader(self, lines, line):
    if ' - ' not in lines[line]:
      self.setName(lines[line].strip())
    else:
      lineContents = lines[line].strip().split(' - ')
      self.setArtist(lineContents[0])
      self.setName(lineContents[1])
    return (line + 1)
    
  def loadPlainDescription(self, lines, line):
    # while there is more than four spaces (not verse)
    # and we are not in the chord line of the first verse
    while (lines[line].startswith(self.PLAIN_DESC_PREFIX) and
     not lines[line+1][:4].strip()):
      self.addDesc(lines[line].strip().replace('#', '\\shrp{}'))
      line += 1
    return line
  
  def loadPlainText(self, lines, line):
    num = 1
    leftHang = self.calcLeftHang(lines[line:])
    while line < len(lines):
      line = self.skipWhiteLines(lines, line)
      if line < len(lines):
        line = self.loadPlainVerse(lines, line, num, leftHang)
        num += 1
  
  def calcLeftHang(self, lines):
    hangs = [len(line) - len(line.lstrip()) for line in lines]
    return statistics.mode(hangs)
  
  def loadPlainVerse(self, lines, line, num, leftHang):
    verse = Verse(num, leftHang)
    line = verse.loadPlain(lines, line)
    self.addVerse(verse)
    return line
    
  def setArtist(self, artist):
    self.artist = artist.replace('&', '\\&')
  
  def setName(self, name):
    self.name = name
  
  def addDesc(self, line):
    if line.startswith('Capo'):
      self.desc.append('\\capo{' + line[5:] + '}')
    elif line.startswith('(Capo'):
      self.desc.append('\\capo{' + line[5:-1] + '}')
    elif line.startswith('P'):
      self.desc.append('\\pick{' + line + '}')
    else:
      self.desc.append('\\musicnote{' + line + '}')
  
  def addVerse(self, verse):
    self.verses.append(verse)
    self.chords.update(verse.getChords())
  
  def outPlain(self):
    outStr = ('\n        {artist} - {title}\n\n'.format(self.name, self.artist) + 
      '\n     '.join(self.outDescPlain()) + '\n' + 
      '\n\n'.join(verse.outPlain() for verse in self.verses))
  
  def outDescPlain(self):
    for line in self.desc:
      if line.startswith('\\capo'):
        yield 'Capo ' + line[6:-1]
      elif line.startswith('\\pick'):
        yield line[6:-1]
      else:
        yield line
  
  def outTex(self):
    outStr = '\\beginsong{' + self.name + '}'
    if self.artist: outStr += '[by={' + self.artist + '}]'
    outStr += '\n'
    for desc in self.desc: outStr += (desc + '\n')
    for verse in self.verses: outStr += verse.outTex()
    return outStr + '\endsong\n\n\n'


class Verse:
  INIT_MARK = '\\['
  END_MARK = ']'

  def __init__(self, order, leftHang):
    self.quotes = False
    self.empty = False
    self.chordCache = ''
    self.isFirst = (order == 1)
    self.lines = []
    self.chordsOn = (order == 1)
    self.chords = set()
    self.leftHang = leftHang
  
  def loadPlain(self, lines, line):
    self.loadMark(lines, line)
    initLine = True # first line
    while True:
      if line == len(lines):
        break # end of song
      content = lines[line][self.leftHang:].rstrip()
      if not content.strip(): # no line content
        if initLine:
          self.setEmpty() # if first line, verse is empty
        break
      # analyse if the line is chord or text
      if self.isChordLine(content):       
        self.addPlainChordLine(content)
      else:
        self.addPlainTextLine(content)
      line += 1
      initLine = False
    line += 1
    self.end()
    return line
  
  def isChordLine(self, content):
    words = content.split()
    wordCaps = [int(word[0].isupper()) for word in words]
    wordLengths = [len(word) for word in words]
    nonCaps = len(wordCaps) - sum(wordCaps)
    wordLen = sum(wordLengths) / len(wordLengths)
    for char in content:
      if char in conf.get('chordlinemarkers'):
        lineMarker = True
        break
    else:
      lineMarker = False
    return ('#' in content or (nonCaps == 0 and (wordLen < 4 or lineMarker)))


  def loadMark(self, lines, line):
    init = lines[line][:self.leftHang].strip() # load first line prefix (verse mark)
    # if the first line has a mark (not a chord line) or is the last one
    if init or (line + 1) == len(lines) or not lines[line+1].strip():
      mark = init[:-1]
    else:
      mark = lines[line+1].split()[0][:-1]
    self.setMark(mark)
  
  def setMark(self, mark):
    self.initMark = mark
    print(mark, end='')
    if mark.isnumeric():
      self.numeric = True
      self.mark = '\\num'
    elif mark in conf.get('marks').keys():
      self.numeric = False
      self.mark = conf.get('marks', mark)
    else:
      self.numeric = False
      self.mark = '\\freev'
  
  def addPlainChordLine(self, line):
    if self.chordCache:
      self.chordOnlyLine()
    self.chordCache = line
  
  def addPlainTextLine(self, line):
    if self.chordCache:
      line = self.mergeLines(line.replace(' - ', '~- '), self.chordCache)
      self.chordCache = ''
      self.turnOnChords()
    else:
      self.turnOffChords()
      line = line.replace(' - ', '~- ')
    i = 0
    while i < len(line):
      if line[i] == '"':
        if self.quotes:
          self.quotes = False
          line = line[:i] + '}' + line[(i+1):]
        else:
          self.quotes = True
          line = line[:i] + '\\uv{' + line[(i+1):]
      i += 1
    for key in conf.get('textsubs').keys():
      line = line.replace(key, conf.get('textsubs', key))
    self.lines.append(line)
  
  def end(self):
    if self.quotes:
      self.lines.append('}')
    if self.chordCache:
      self.chordOnlyLine()
  
  def setEmpty(self):
    self.empty = True
    if self.mark.startswith('\\chor'):
      self.mark = self.mark.replace('\\chorus', '\\repchorus').replace('\\chor', '\\repchorus') + '{\\emptyspace}'
    elif self.mark == '\\num':
      self.mark = '\\repsec{' + self.initMark + '}{\emptyspace}'
    else:
      for x in ('\\intro', '\\solo', '\\bridge', '\\averse', '\\bverse', '\\cverse'):
        if self.mark.startswith(x):
          self.mark += '\emptyspace\\\\ \cl'
          break
      else:
        self.mark = '\\error'
  
  def chordOnlyLine(self):
    if not self.chordsOn:
     self.turnOnChords()
    chords = [self.chordMark(chord) for chord in self.chordCache.split()]
    self.lines.append('\\cseq{' + ' '.join(chords) + '}\\\\')
  
  def chordMark(self, chord):
    for sub in conf.get('chordsubs').keys():
      chord = chord.replace(sub, conf.get('chordsubs', sub))
    self.chords.add(chord)
    return self.INIT_MARK + chord + self.END_MARK
  
  def turnOnChords(self):
    if not self.chordsOn:
      self.chordsOn = True
      if self.lines and self.lines[-1] == '\\chordsoff':
        self.lines = self.lines[:-1]
      else:
        self.lines.append('\\chordson')
  
  def turnOffChords(self):
    if self.chordsOn:
      self.chordsOn = False
      if self.lines and self.lines[-1] == '\\chordson':
        self.lines = self.lines[:-1]
      else:
        self.lines.append('\\chordsoff')
  
  # slouci radku akordu a textu
  def mergeLines(self, textLine, chordLine):
    finLine = ''
    # jak je dlouha radka (vizualne)
    lineLen = max(len(chordLine), len(textLine))
    # doplneni mezerami
    if len(textLine) < lineLen:
      textLine += ' ' * (lineLen - len(textLine))
    elif len(chordLine) < lineLen:
      chordLine += ' ' * (lineLen - len(chordLine))
    i = 0
    join = -1
    # dokud nejsem na konci
    while i < lineLen:
      j = 0
      # nasaj akord
      while (i + j) < len(chordLine) and chordLine[i+j] != ' ':
        j += 1
      # neni akord, posun se o 1
      if j == 0:
        if textLine[i] == ' ' and join > 1:
          finLine += '}'
          join = -1
        elif join != -1: join += 1
        finLine += textLine[i]
        i += 1
      # je akord, vypust ho spolu s textem pod nim a posun se
      else:
        if join != -1:
          if finLine[-1] == ' ':
            finLine = finLine[:-1] + '} '
          else:
            finLine += '}'
          join = -1
        finLine += self.chordMark(chordLine[i:(i+j)])
        nextSpace = textLine[(i+j):].rstrip().find(' ')
        nextChord = len(chordLine[(i+j):]) - len(chordLine[(i+j):].lstrip())
        hasOnlySpacesUnder = (textLine[i:(i+j)] == (' ' * j))
        isSpaceNext = (nextSpace == 0 or nextSpace == 1)
        if (' ' in textLine[i:(i+j)] and not hasOnlySpacesUnder) or (isSpaceNext and (nextChord != nextSpace + 1)):
          join = 0
          finLine += '{'
        finLine += textLine[i:(i+j)]
        i += j
    if join != -1:
      finLine = finLine.rstrip() + '}'
    return finLine.strip()
  
  def ending(self):
    ending = '\n'
    if not self.empty:
      if self.numeric:
        ending += '\\fin\n'
      else:
        ending += '\\cl\n'
    if self.isFirst: ending += '\\chordsoff\n'
    return ending
  
  def outTex(self):
    outStr = self.mark + ('\n' if not self.empty else '')
    if self.lines:
      outStr += '\n'.join(self.lines)
    outStr += self.ending()
    return outStr
  
  def outPlain(self):
    if self.lines:
      lineno = 1
      lines = []
      for line in self.lines:
        line = line.replace('{', '').replace('}', '')
        chordline = ''
        textline = ''
        if '\\[' in line:
          chordline = ' ' * 4
          textline = (self.plainMark().ljust(4) if lineno == 1 else ' ' * 4)
          parts = line.split('\\[')
          textline += parts[0]
          for part in parts:
            chord, text = part.split(']')
            diff = len(text) - len(chord)
            if diff > 0:
              chordline += chord + ' ' * diff
              textline += text
            else:
              addtextspace = -diff + 1
              chordline += chord + ' '
              textline += text
              if text[-1] == ' ':
                textline += ' ' * (addtextspace)
              else:
                textline += '-'.ljust(addtextspace)
        else:
          textline = line
        if chordline:
          lines.append(chordline)
        lines.append(textline)
        lineno += 1
    else:
      return self.plainMark()
  
  def plainMark(self):
    return self.initMark + '.'
  
  def getChords(self):
    return self.chords

    
class Config:
  def __init__(self, fileName):
    with open(fileName, encoding='utf8') as confjson:
      self._config = json.load(confjson, object_pairs_hook=collections.OrderedDict)
  
  def get(self, *args):
    val = self._config
    for arg in args:
      val = val[arg]
    return val

conf = Config(os.path.join(os.path.dirname(sys.argv[0]), 'conf.json'))

def songToFile(fnIn, outfile):
  song = Song()
  song.readPlain(fnIn)
  outfile.write(song.outTex())

if __name__ == '__main__':
  if len(sys.argv) == 2:
    fout = open('zpevnik.tex', 'w', encoding='utf8')
    fout.write(open('init.tex', encoding='utf8').read())
  else:
    fout = None
  for fn in sorted(os.listdir(sys.argv[1]), key=locale.strxfrm):
    try:
      if '.txt' not in fn: continue
      if fout:
        songToFile(os.path.join(sys.argv[1], fn), fout)
      else:
        with open(os.path.join(sys.argv[2], fn.replace('.txt', '.tex')), 'w', encoding='utf8') as onefile:
          songToFile(os.path.join(sys.argv[1], fn), onefile)
    except:
      print(fn)
      raise
  if fout:
    fout.write('\n\\end{songs}\n\\end{document}\n')
    fout.close()
  