import sys, re, os

IN_REGEX = r'\\musicnote\{\\pick\{(.*?)\}\}'
OUT_REGEX = r'\pick{\1}'
for fn in os.listdir(sys.argv[1]):
  path = os.path.join(sys.argv[1], fn)
  with open(path, encoding='utf8') as file:
    cnt = file.read()
    cnt = re.sub(IN_REGEX, OUT_REGEX, cnt)
  with open(path, 'w', encoding='utf8') as file:
    file.write(cnt)