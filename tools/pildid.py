#!/usr/bin/env python3
"""Genereerib public/pildid/ sisu lahtematerjal/ kaustast.

Lahtematerjal on Kadi Koristab OU oma fotod, mis on avaldatud hange.ee
ettevotte lehel ja Facebookis. Skript loikab enne/parast paarid kaheks,
eemaldab vesimargiribad, kustutab EXIF-i ja salvestab WebP kujul.

Kaivitamine:  python3 tools/pildid.py
Tulemus on korratav: kaks kaivitust annavad baidi pealt sama tulemuse.
"""

import hashlib
import math
import os
import shutil

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLIKAS = os.path.join(JUUR, "lahtematerjal")
VALJUND = os.path.join(JUUR, "public", "pildid")
FONT = os.path.join(JUUR, "public", "fondid", "fraunces-latin.woff2")

ROHELINE = (47, 107, 79)
PAIKE = (245, 192, 68)
TINT = (245, 247, 242)

# fail, telg, vesimargiriba korgus, sihtlaius, korgusekarbe, nimi, laad
#
# laad "liugur" tahendab, et enne ja parast pannakse lehel uheks pildiks,
# mille peal saab kaepidet lohistada. Selleks peavad kaks kaadrit olema
# kohakuti, seega need paarid joondatakse enne salvestamist ara.
# laad "paar" tahendab kahte fotot korvuti. Sinna lahevad need, kus
# kaadrid on liiga erineva suuruse ja nurga alt, et neid uheks ajada.
PAARID = [
    ("fb01.jpg", "y", 0, 1100, None, "vannitoa-porand", "liugur"),
    ("g65031.jpg", "x", 45, 428, None, "wc-ruum", "paar"),
    ("g65032.jpg", "x", 45, 428, None, "dusinurk", "paar"),
    ("g65033.jpg", "x", 45, 428, None, "koogi-toopind", "liugur"),
    ("g65034.jpg", "x", 45, 428, None, "kulmkapp", "paar"),
    ("g65037.jpg", "x", 46, 449, 881, "aken-vaade", "liugur"),
    ("g65038.jpg", "y", 45, 870, None, "ovaalne-aken", "liugur"),
]

YKSIKUD = [("fb09.jpg", 900, "raamaturiiul")]


def ava(nimi):
    im = Image.open(os.path.join(ALLIKAS, nimi))
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def jooksud(indeksid):
    valja, algus, eelmine = [], None, None
    for i in indeksid:
        if algus is None:
            algus = i
        elif i != eelmine + 1:
            valja.append((algus, eelmine))
            algus = i
        eelmine = i
    if algus is not None:
        valja.append((algus, eelmine))
    return valja


def poolita(nimi, telg, vesimark):
    """Loikab liitpildi kaheks: enne ja parast."""
    im = ava(nimi)
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    korgus = h - vesimark
    keha = a[:korgus]

    veerg_min = keha.min(axis=(0, 2))
    aare = 0
    while aare < 40 and veerg_min[aare] > 238:
        aare += 1

    x0, y0, x1, y1 = aare, aare, w - aare, korgus
    sisu = a[y0:y1, x0:x1]
    telje_min = sisu.min(axis=(0, 2)) if telg == "x" else sisu.min(axis=(1, 2))
    valged = [i for i, v in enumerate(telje_min) if v > 238]
    kandidaadid = [
        r for r in jooksud(valged)
        if 0.3 * len(telje_min) < r[0] < 0.7 * len(telje_min)
    ]
    if kandidaadid:
        algus, lopp = max(kandidaadid, key=lambda r: r[1] - r[0])
    else:
        keskkoht = len(telje_min) // 2
        algus, lopp = keskkoht, keskkoht

    if telg == "x":
        esimene = im.crop((x0, y0, x0 + algus, y1))
        teine = im.crop((x0 + lopp + 1, y0, x1, y1))
    else:
        esimene = im.crop((x0, y0, x1, y0 + algus))
        teine = im.crop((x0, y0 + lopp + 1, x1, y1))

    laius = min(esimene.size[0], teine.size[0])
    korgus2 = min(esimene.size[1], teine.size[1])
    return (esimene.crop((0, 0, laius, korgus2)),
            teine.crop((0, 0, laius, korgus2)))


def servajoon(im, laius=240):
    """Halltoonides servade tugevus, keskmine null ja hajuvus uks.

    Servad, mitte varvid, sest enne ja parast pildil on varvid just need,
    mis muutuvad. Vuugid, raamid ja aarejooned jaavad samaks.
    """
    tegur = laius / im.size[0]
    hall = im.convert("L").resize(
        (laius, max(1, round(im.size[1] * tegur))), Image.LANCZOS)
    a = np.asarray(hall).astype(float)
    gx = np.zeros_like(a)
    gy = np.zeros_like(a)
    gx[:, 1:-1] = a[:, 2:] - a[:, :-2]
    gy[1:-1, :] = a[2:, :] - a[:-2, :]
    m = np.hypot(gx, gy)
    return (m - m.mean()) / (m.std() + 1e-6)


def joonda(enne, parast, laius=240):
    """Nihutab kaks kaadrit kohakuti ja karbib mõlemad uhisele osale.

    Telefon ei olnud kahe vottega tapselt samas kohas. Otsime nihke, mille
    juures servad koige paremini kattuvad, ja loikame molemalt sama palju
    ara. Ainult paralleelnihe: suumi ja poorde erinevust see ei paranda,
    sellepart on osa paare lehel korvuti, mitte liugurina.
    """
    A = servajoon(enne, laius)
    B = servajoon(parast, laius)
    h, w = A.shape
    ulatus = int(0.16 * laius)
    parim = (-9.0, 0, 0)
    for dy in range(-ulatus, ulatus + 1):
        for dx in range(-ulatus, ulatus + 1):
            a = A[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
            b = B[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
            if a.size < 0.4 * A.size:
                continue
            skoor = float((a * b).mean())
            if skoor > parim[0]:
                parim = (skoor, dx, dy)

    skoor, dx, dy = parim
    tegur = enne.size[0] / laius
    DX, DY = round(dx * tegur), round(dy * tegur)
    W, H = enne.size
    x0, y0 = max(0, DX), max(0, DY)
    x1, y1 = W + min(0, DX), H + min(0, DY)
    return (enne.crop((x0, y0, x1, y1)),
            parast.crop((x0 - DX, y0 - DY, x1 - DX, y1 - DY)),
            skoor, DX, DY)


def salvesta(im, nimi, sihtlaius, korgusepiir=None, kvaliteet=78):
    """Ei suurenda kunagi. Kui fail laheb ule 400 KB, vahendab laiust."""
    if korgusepiir and im.size[1] > korgusepiir:
        im = im.crop((0, 0, im.size[0], korgusepiir))
    if im.size[0] > sihtlaius:
        uus_korgus = round(im.size[1] * sihtlaius / im.size[0])
        im = im.resize((sihtlaius, uus_korgus), Image.LANCZOS)
    puhas = Image.new("RGB", im.size)
    puhas.putdata(list(im.getdata()))
    tee = os.path.join(VALJUND, nimi + ".webp")
    while True:
        puhas.save(tee, "WEBP", quality=kvaliteet, method=6)
        if os.path.getsize(tee) <= 400 * 1024 or puhas.size[0] < 400:
            break
        uus = int(puhas.size[0] * 0.85)
        puhas = puhas.resize((uus, round(puhas.size[1] * uus / puhas.size[0])),
                             Image.LANCZOS)
    return tee, puhas.size


def kirjatuup(suurus):
    try:
        return ImageFont.truetype(FONT, suurus)
    except OSError:
        return ImageFont.load_default()


def bezier(p0, p1, p2, p3, samme=48):
    """Kuupbezier punktideks. PIL ei oska kovereid, seega arvutame ise."""
    valja = []
    for i in range(samme + 1):
        t = i / samme
        u = 1 - t
        valja.append((
            u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
        ))
    return valja


def kaar(kese, raadius, kraadi_algus, kraadi_lopp, samme=48):
    """Ringikaare punktid. Nurk kaib kellaosuti suunas, y kasvab allapoole."""
    valja = []
    for i in range(samme + 1):
        kraad = kraadi_algus + (kraadi_lopp - kraadi_algus) * i / samme
        nurk = math.radians(kraad)
        valja.append((kese[0] + raadius * math.cos(nurk),
                      kese[1] + raadius * math.sin(nurk)))
    return valja


def ikoon(kylg):
    """Veepiisk, sama kuju mis public/favicon.svg.

    Roheline plaat, soe kollane piisk ja valge valguskaar piisa sees.
    Kuju on SVG-s beziertega, siin punkthaaval sama joon.
    """
    m = 12
    s = kylg * m

    def y(v):
        return v * s / 64.0

    def teisenda(punktid):
        return [(y(a), y(b)) for a, b in punktid]

    # Labipaistva osa RGB on sama mis plaadil, muidu jookseb vahendamisel
    # umarate nurkade servadesse must aariake.
    plaat = Image.new("RGBA", (s, s), ROHELINE + (0,))
    ImageDraw.Draw(plaat).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=y(17), fill=ROHELINE + (255,))

    piisk = (bezier((32, 11), (33.5, 17), (47, 28.5), (47, 39))
             + kaar((32, 39), 15, 0, 180)
             + bezier((17, 39), (17, 28.5), (30.5, 17), (32, 11)))
    ImageDraw.Draw(plaat).polygon(teisenda(piisk), fill=PAIKE + (255,))

    laige = teisenda(kaar((32, 39), 9.5, 195, 138))
    jl = ImageDraw.Draw(plaat)
    jl.line(laige, fill=(255, 255, 255, 255), width=int(y(5)), joint="curve")
    for kx, ky in (laige[0], laige[-1]):
        r = y(2.5)
        jl.ellipse([kx - r, ky - r, kx + r, ky + r], fill=(255, 255, 255, 255))

    return plaat.resize((kylg, kylg), Image.LANCZOS)


def jagamispilt(alus):
    """1200x630 jagamispilt: foto vasakul, tekstiplokk paremal."""
    lm = Image.new("RGB", (1200, 630), TINT)
    foto = ImageOps.fit(alus, (700, 630), Image.LANCZOS, centering=(0.5, 0.5))
    lm.paste(foto, (0, 0))
    j = ImageDraw.Draw(lm)
    j.rectangle([700, 0, 1200, 630], fill=ROHELINE)
    j.rectangle([700, 0, 712, 630], fill=PAIKE)
    margis = ikoon(88)
    lm.paste(margis, (752, 128), margis)
    j.text((752, 246), "Kadi koristab", font=kirjatuup(58), fill=(255, 255, 255))
    j.text((752, 332), "Kodud, kontorid ja", font=kirjatuup(30), fill=(214, 232, 220))
    j.text((752, 374), "ehitusjärgne koristus", font=kirjatuup(30), fill=(214, 232, 220))
    j.text((752, 434), "Saaremaal", font=kirjatuup(30), fill=PAIKE)
    return lm


def main():
    if os.path.isdir(VALJUND):
        shutil.rmtree(VALJUND)
    os.makedirs(VALJUND)

    logi = []
    for fail, telg, vesimark, laius, korgus, nimi, laad in PAARID:
        enne, parast = poolita(fail, telg, vesimark)
        if laad == "liugur":
            enne, parast, skoor, DX, DY = joonda(enne, parast)
            print("joondus %-16s skoor %.2f  nihe dx=%d dy=%d" % (nimi, skoor, DX, DY))
        for pilt, silt in ((enne, "enne"), (parast, "parast")):
            tee, suurus = salvesta(pilt, "%s-%s" % (nimi, silt), laius, korgus)
            logi.append((os.path.basename(tee), suurus, os.path.getsize(tee)))

    for fail, laius, nimi in YKSIKUD:
        tee, suurus = salvesta(ava(fail), nimi, laius)
        logi.append((os.path.basename(tee), suurus, os.path.getsize(tee)))

    jp = jagamispilt(ava(YKSIKUD[0][0]))
    jp_tee = os.path.join(VALJUND, "jagamispilt.jpg")
    jp.save(jp_tee, "JPEG", quality=86, optimize=True)
    logi.append(("jagamispilt.jpg", jp.size, os.path.getsize(jp_tee)))

    juur = os.path.join(JUUR, "public")
    ikoon(180).save(os.path.join(juur, "apple-touch-icon.png"), "PNG", optimize=True)
    ikoon(64).save(os.path.join(juur, "favicon.ico"), "ICO",
                   sizes=[(16, 16), (32, 32), (48, 48)])

    print("%-34s %-12s %s" % ("fail", "mootmed", "baiti"))
    for nimi, suurus, baiti in logi:
        print("%-34s %-12s %d" % (nimi, "%dx%d" % suurus, baiti))

    h = hashlib.sha256()
    for nimi in sorted(os.listdir(VALJUND)):
        h.update(open(os.path.join(VALJUND, nimi), "rb").read())
    print("\nkontrollsumma", h.hexdigest())


if __name__ == "__main__":
    main()
