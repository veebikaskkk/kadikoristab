#!/usr/bin/env python3
"""Kontrollnimekiri koodiga. Kaivitamine: python3 tools/kontroll.py"""
import io, json, os, re, sys
from html.parser import HTMLParser
from PIL import Image

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(JUUR, "public")
vead = []
def viga(t): vead.append(t)

TYHI = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

class Kontroll(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pinu, self.h, self.imgs, self.stiil, self.lingid, self.idd = [], [], [], [], [], []
    def handle_starttag(self, tag, attrs, ise_sulguv=False):
        d = dict(attrs)
        if "style" in d: self.stiil.append(tag)
        if tag == "img": self.imgs.append(d)
        if tag in ("h1","h2","h3","h4","h5","h6"): self.h.append(int(tag[1]))
        if tag == "a" and d.get("href"): self.lingid.append(d["href"])
        if tag in ("link","script") and (d.get("href") or d.get("src")):
            self.lingid.append(d.get("href") or d.get("src"))
        if d.get("id"): self.idd.append(d["id"])
        if tag not in TYHI and not ise_sulguv: self.pinu.append(tag)
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs, True)
    def handle_endtag(self, tag):
        if tag in TYHI: return
        if not self.pinu or self.pinu[-1] != tag:
            viga("sildid ei ole tasakaalus: /%s, avatud %s" % (tag, self.pinu[-5:]))
            if tag in self.pinu:
                while self.pinu and self.pinu.pop() != tag: pass
        else:
            self.pinu.pop()

kasutatud = set()
for lehefail in ("index.html", "404.html"):
    tee = os.path.join(PUB, lehefail)
    s = io.open(tee, encoding="utf-8").read()
    k = Kontroll(); k.feed(s); k.close()
    if k.pinu: viga("%s: sulgemata sildid %s" % (lehefail, k.pinu))
    if k.stiil: viga("%s: style= atribuut siltidel %s" % (lehefail, k.stiil))
    if k.h.count(1) != 1: viga("%s: h1 arv on %d" % (lehefail, k.h.count(1)))
    eelmine = 0
    for t in k.h:
        if eelmine and t > eelmine + 1: viga("%s: pealkirjatase huppab h%d -> h%d" % (lehefail, eelmine, t))
        eelmine = t
    if "—" in s: viga("%s: pikk mottekriips" % lehefail)
    for m in re.finditer(r"\[[A-ZÕÄÖÜ][A-ZÕÄÖÜ /]{2,}\]", s):
        viga("%s: kohatait %s" % (lehefail, m.group(0)))
    for m in re.finditer(r",\s+(ja|ning|või|ega)\s", s):
        viga("%s: koma rinnastava sidesona ees: ...%s..." % (lehefail, s[max(0,m.start()-45):m.end()]))
    for blokk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: json.loads(blokk)
        except Exception as e: viga("%s: JSON-LD katki: %s" % (lehefail, e))
    for i in k.imgs:
        src = i.get("src","")
        kasutatud.add(src.lstrip("/"))
        f = os.path.join(PUB, src.lstrip("/"))
        if not os.path.exists(f): viga("%s: pilti ei ole: %s" % (lehefail, src)); continue
        w, h = Image.open(f).size
        if str(w) != i.get("width") or str(h) != i.get("height"):
            viga("%s: %s mootmed failis %dx%d, HTML-is %sx%s" % (lehefail, src, w, h, i.get("width"), i.get("height")))
        if not i.get("alt"): viga("%s: alt-tekst puudub: %s" % (lehefail, src))
        if os.path.getsize(f) > 400*1024: viga("%s on ule 400 KB" % src)
    for href in k.lingid:
        if href.startswith("#"):
            if href[1:] not in k.idd: viga("%s: ankur ei vasta millelegi: %s" % (lehefail, href))
        elif href.startswith("/"):
            kasutatud.add(href.lstrip("/"))
            if not os.path.exists(os.path.join(PUB, href.lstrip("/"))):
                viga("%s: sisemine link katki: %s" % (lehefail, href))

css = io.open(os.path.join(PUB, "stiil.css"), encoding="utf-8").read()
for m in re.finditer(r'url\("(/[^"]+)"\)', css):
    kasutatud.add(m.group(1).lstrip("/"))
    if not os.path.exists(os.path.join(PUB, m.group(1).lstrip("/"))):
        viga("stiil.css: puuduv fail %s" % m.group(1))

# og:image ja manifest
idx = io.open(os.path.join(PUB, "index.html"), encoding="utf-8").read()
og = re.search(r'property="og:image" content="https://[^/]+/([^"]+)"', idx)
if not og or not os.path.exists(os.path.join(PUB, og.group(1))):
    viga("og:image faili ei ole")
else:
    kasutatud.add(og.group(1))
    w, h = Image.open(os.path.join(PUB, og.group(1))).size
    if (w, h) != (1200, 630): viga("og:image on %dx%d, peab olema 1200x630" % (w, h))

for m in re.finditer(r'"src": "/([^"]+)"', io.open(os.path.join(PUB,"site.webmanifest"), encoding="utf-8").read()):
    kasutatud.add(m.group(1))
sm = io.open(os.path.join(PUB, "sitemap.xml"), encoding="utf-8").read()
for m in re.finditer(r"<image:loc>https://[^/]+/([^<]+)</image:loc>", sm):
    kasutatud.add(m.group(1))
    if not os.path.exists(os.path.join(PUB, m.group(1))): viga("sitemap viitab puuduvale pildile %s" % m.group(1))
kasutatud |= {"index.html","404.html","robots.txt","sitemap.xml","_headers","_redirects",
              "site.webmanifest","favicon.ico","favicon.svg","apple-touch-icon.png",
              "stiil.css","skript.js"}
olemas = set()
for j, _, failid in os.walk(PUB):
    for f in failid:
        olemas.add(os.path.relpath(os.path.join(j, f), PUB))
kasutu = sorted(olemas - kasutatud)
if kasutu: viga("public/ sees on kasutuseta failid: %s" % kasutu)

print("Kontrollitud: %d faili public/ sees" % len(olemas))
if vead:
    print("\nVEAD (%d):" % len(vead))
    for v in vead: print(" -", v)
    sys.exit(1)
print("Koik kontrollid labitud.")
