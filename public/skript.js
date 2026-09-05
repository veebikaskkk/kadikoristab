/* Kadi koristab. Kaks asja: enne ja parast liugur ning menyy aktiivne link. */
(function () {
  "use strict";

  /* Enne ja parast liugur.

     Natiivne <input type="range"> uksi ei kolba: puuteekraanil ei hyppa ta
     sinna, kuhu vajutad, vaid noaub tapselt poidla tabamist, ja meie poial
     on labipaistev. Seetottu on lohistus siin ise kirjutatud.

     Input jaab alles klaviatuuri ja ekraanilugeja jaoks, aga pointer-events
     on tal maas, nii et puuted joauvad kasti endani.

     Puutel ei haarata zesti kohe. Ootame, kumb suund voidab: kui sorm
     liigub rohkem kylili, votame lohistuse endale, kui pusti, laseme lehel
     rahulikult edasi kerida. Konteineri touch-action: pan-y hoiab selle
     ara, et brauser kylili kerima hakkaks. */
  function seaLiugurid() {
    var kastid = document.querySelectorAll("[data-vordlus]");
    Array.prototype.forEach.call(kastid, function (kast) {
      var liugur = kast.querySelector(".vordlus-liugur");
      if (!liugur) { return; }

      var algusX = 0;
      var algusY = 0;
      var otsustatud = false;
      var lohistab = false;
      var osuti = null;

      function sea(protsent) {
        var v = Math.max(0, Math.min(100, protsent));
        kast.style.setProperty("--pos", v + "%");
        liugur.value = Math.round(v);
      }

      function protsendiks(x) {
        var raam = kast.getBoundingClientRect();
        return raam.width ? ((x - raam.left) / raam.width) * 100 : 50;
      }

      function haara(e) {
        lohistab = true;
        kast.classList.add("lohistab");
        try { kast.setPointerCapture(osuti); } catch (viga) { /* vana brauser */ }
      }

      liugur.addEventListener("input", function () {
        sea(Number(liugur.value));
      });

      kast.addEventListener("pointerdown", function (e) {
        if (e.button > 0) { return; }
        osuti = e.pointerId;
        algusX = e.clientX;
        algusY = e.clientY;
        otsustatud = e.pointerType === "mouse";
        lohistab = false;
        if (otsustatud) {
          haara(e);
          sea(protsendiks(e.clientX));
        }
      });

      kast.addEventListener("pointermove", function (e) {
        if (osuti === null || e.pointerId !== osuti) { return; }
        if (!otsustatud) {
          var dx = Math.abs(e.clientX - algusX);
          var dy = Math.abs(e.clientY - algusY);
          if (dx < 5 && dy < 5) { return; }
          otsustatud = true;
          if (dx <= dy) { osuti = null; return; }
          haara(e);
        }
        if (lohistab) {
          if (e.cancelable) { e.preventDefault(); }
          sea(protsendiks(e.clientX));
        }
      });

      function lopeta(e) {
        if (osuti === null || (e && e.pointerId !== osuti)) { return; }
        if (!lohistab && e && e.type === "pointerup") {
          sea(protsendiks(e.clientX));
        }
        try { kast.releasePointerCapture(osuti); } catch (viga) { /* juba vabas */ }
        kast.classList.remove("lohistab");
        osuti = null;
        lohistab = false;
        otsustatud = false;
      }

      kast.addEventListener("pointerup", lopeta);
      kast.addEventListener("pointercancel", lopeta);
      kast.addEventListener("dragstart", function (e) { e.preventDefault(); });

      sea(Number(liugur.value));
    });
  }

  function seaMenyy() {
    var lingid = document.querySelectorAll(".menyy a[href^='#']");
    if (!lingid.length || !("IntersectionObserver" in window)) { return; }

    var kaart = {};
    var jalgitavad = [];
    Array.prototype.forEach.call(lingid, function (link) {
      var sihtmark = document.getElementById(link.getAttribute("href").slice(1));
      if (sihtmark) {
        kaart[sihtmark.id] = link;
        jalgitavad.push(sihtmark);
      }
    });

    var vaatleja = new IntersectionObserver(function (kirjed) {
      kirjed.forEach(function (kirje) {
        var link = kaart[kirje.target.id];
        if (!link) { return; }
        if (kirje.isIntersecting) {
          Array.prototype.forEach.call(lingid, function (m) {
            m.removeAttribute("aria-current");
          });
          link.setAttribute("aria-current", "true");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px", threshold: 0 });

    jalgitavad.forEach(function (sihtmark) { vaatleja.observe(sihtmark); });
  }

  function kaivita() {
    seaLiugurid();
    seaMenyy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", kaivita);
  } else {
    kaivita();
  }
})();
