/* Kadi koristab. Kaks asja: enne ja parast liugur ning menyy aktiivne link. */
(function () {
  "use strict";

  function seaLiugurid() {
    var kastid = document.querySelectorAll("[data-vordlus]");
    Array.prototype.forEach.call(kastid, function (kast) {
      var liugur = kast.querySelector(".vordlus-liugur");
      if (!liugur) { return; }
      function uuenda() {
        kast.style.setProperty("--pos", liugur.value + "%");
      }
      liugur.addEventListener("input", uuenda);
      liugur.addEventListener("change", uuenda);
      uuenda();
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
