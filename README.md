# Kadi koristab, üheleheline koduleht

KADI KORISTAB OÜ koduleht. Puhas HTML, CSS ja JavaScript, ilma raamistiku ja
ehitusprotsessita. Majutus Cloudflare Workeri peal.

## Failid

    public/            kõik, mis brauserisse jõuab
      index.html       ainus sisuleht
      404.html         veateade
      stiil.css        kogu kujundus
      skript.js        enne ja pärast liugur, menüü aktiivne link
      pildid/          WebP fotod ja jagamispilt
      fondid/          Fraunces ja Nunito Sans, latin ja latin-ext
      _headers         turvapäised ja vahemälu
      _redirects       vanade aadresside ümbersuunamine
      robots.txt, sitemap.xml, site.webmanifest, favicon.*
    worker.js          eelvaate aadressile X-Robots-Tag, muidu staatiline
    wrangler.jsonc     Cloudflare seadistus
    tools/pildid.py    genereerib public/pildid/ sisu
    tools/kontroll.py  käib kontrollnimekirja koodiga läbi
    lahtematerjal/     lähtefotod, ei lähe Giti ega serverisse

## Mida on vaja enne avaldamist asendada

1. **Domeen.** Kood eeldab aadressi `https://kadikoristab.ee/`. See on
   valitud pakkumise põhjal ega ole kliendiga kinnitatud. Kui päris domeen
   on teine, asenda kõikides failides korraga:

       grep -rl "kadikoristab.ee" public | xargs sed -i '' "s/kadikoristab.ee/UUS-DOMEEN.ee/g"

   Puudutab: index.html canonical ja Open Graph, JSON-LD, robots.txt,
   sitemap.xml.
2. **KMKR number.** Praegu jalusel puudub, sest andmetes seda ei olnud. Kui
   ettevõte on käibemaksukohustuslane, lisa number `public/index.html`
   jalusesse ja `worker.js` ei vaja muudatust.

## Mida on kliendilt veel vaja küsida

- Kas jaluses tohib olla Tehnika tn 2-56 kui juriidiline aadress, või tuleks
  näidata ainult tegevuspiirkonda. Praegu on aadress jaluses.
- Kliendi tagasiside tsitaadid. Praegu lehel ühtegi ei ole, sest ühtegi ei
  olnud antud. Kaks kuni kolm lauset koos eesnime ja asulaga oleks kõige
  tugevam lisandus.
- Hinnad või hinnavahemik, kui neid tohib avaldada. Praegu lehel hindu ei ole.
- Paremad fotod. Praegused pärinevad hange.ee ettevõtte lehelt ja Facebookist
  ning on telefoniga tehtud. Üks selge pilt Kadist endast tööd tegemas tõstaks
  usaldust kõige rohkem.

## Pildid

`tools/pildid.py` võtab `lahtematerjal/` kaustast liitpildid, kus enne ja
pärast on ühte faili kõrvuti või kohakuti pandud, lõikab need kaheks,
eemaldab vesimärgiriba, kustutab EXIF-i koos GPS-koordinaatidega ja
salvestab WebP kujul.

    python3 tools/pildid.py

Väljund on korratav: kaks käivitust annavad sama kontrollsumma. Ükski pilt ei
ole üle 400 KB, ühtegi pilti ei suurendata.

## Kontroll

    python3 tools/kontroll.py

Kontrollib koodiga: HTML sildid tasakaalus, täpselt üks h1, pealkirjatasemed
ei hüppa, JSON-LD parsib, sisemised lingid ja ankrud viitavad olemasolevale,
pildi width ja height vastavad failile, alt-tekst olemas, ükski pilt ei ole
üle 400 KB, ühtegi style= atribuuti ei ole, kasutuseta faile ei ole,
og:image on olemas ja 1200x630, pikka mõttekriipsu ei ole, koma ei ole
rinnastava sidesõna ees.

## Kohalik käivitamine

    npx wrangler dev

Ainult see jooksutab `_headers`, `_redirects` ja `not_found_handling`
päriselt. Tavaline staatiline server neid ei loe.

## Avaldamine

    npx wrangler deploy

Esimesel korral seo domeen Cloudflare paneelis Workeri külge.
Cloudflare Web Analytics lülitatakse sisse paneelist, koodi lisada ei ole
vaja ja küpsiseteavitust see kaasa ei too.

## Mõõdud, mis said valitud

- Murdepunktid: 480, 768, 1024 ja 1240 pikslit.
- Palett: roheline #2F6B4F, päikesekollane #F5C044, tekst #1B2A21 taustal
  #F5F7F2. Iga kasutatud värvipaari kontrast on üle 4.5:1.
- Kirjatüübid: Fraunces pealkirjades, Nunito Sans tekstis. Mõlemad omast
  kaustast, latin ja latin-ext, nii et õ ä ö ü ž š on olemas.
- Kujunduslik eripära: kaarja ülaosaga fotod, nagu vana maja aknad.
- Iga töö on aus fotopaar: enne ja pärast kõrvuti, mõlemal oma silt.
  Püstiste fotode paarid on kõrvuti, lamedate omad ülestikku, nii jääb iga
  kaart umbes sama kõrge ja ruudustik püsib sirge.
- Enne ja pärast on lehel kahes vormis ja valiku teeb mõõtmine, mitte
  maitse. `tools/pildid.py` funktsioon `joonda()` otsib iga paari puhul
  nihke, mille juures kahe kaadri servajooned kõige paremini kattuvad, ja
  lõikab mõlemalt sama palju ära. Kui pärast joondamist kattuvus püsib
  kesine, on kaadrid tehtud liiga erineva kauguse ja nurga alt ning ühte
  pilti neist ei saa. Sellised lähevad lehele kõrvuti fotopaarina.
  Mõõdetud kattuvus: ovaalne aken 0.34, köögi tööpind 0.21, vannitoa
  põrand 0.21, aken 0.18 lähevad liuguriks; külmkapp 0.17, dušinurk 0.14,
  WC-ruum 0.12 lähevad paariks. Piir on 0.18.
- Joondus parandab ainult paralleelnihet. Katsetasin ka suumi otsimist,
  aga see andis 0.21 asemel 0.22, ehk mõõdetavalt mitte midagi: kaadrid
  erinevad rohkem kui suumi võrra. Kui kunagi tulevad fotod, kus telefon
  oli mõlemal korral samas kohas, lähevad kattuvusnumbrid üles ja rohkem
  paare kõlbab liuguriks. Laadi saab vahetada `PAARID` tabelis `pildid.py`
  sees, väärtus "liugur" või "paar".
- Liuguri lohistuse teeb `skript.js` ise, pointer-sündmustega, ja
  `<input type="range">` on `pointer-events: none` ning `opacity: 0`.
  Ainult läbipaistvast taustast ei piisanud: natiivne pöial on 52 pikslit
  lai kast, mis istub raja ülaservas ja liigub koos jaotusjoonega, ning osa
  brausereid joonistab talle vaikimisi nähtava serva. Lehel paistis see
  kummalise kastina joone ülaotsas. Fookust näitab nähtav käepide, mis saab
  fookuses rohelise rõnga. Seal on `:focus`, mitte `:focus-visible`, sest
  input ei ole hiirega fokuseeritav ja iga fookus tuleb niikuinii
  klaviatuurilt. Põhjus: puuteekraanil
  ei hüppa natiivne range sinna, kuhu vajutad, vaid nõuab täpselt pöidla
  tabamist, ja meie pöial on läbipaistev. Telefonis jäi liugur seetõttu
  päris seisma. Input on alles klaviatuuri ja ekraanilugeja jaoks ning
  skript hoiab tema `value` sünkroonis, nii et nooleklahvid töötavad.
- Puutel ei haarata žesti kohe. Esimese viie piksli järel vaadatakse, kumb
  suund võidab: külili liigutus võtab lohistuse, püstine jäetakse lehele
  kerimiseks. Ilma selleta oleks pildi kohalt kerimine kinni jäänud.
  Konteineri `touch-action: pan-y` hoiab ära, et brauser külili keriks.
- Nähtav käepide `.vordlus-kaepide` on eraldi element, mitte natiivne
  `::-webkit-slider-thumb`. WebKitis jääb pöial täiskõrgusega raja
  ülaserva kinni ega tsentreeru püsti. Käepide järgib sama `--pos`
  muutujat mis jaotusjoon.
