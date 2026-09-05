/* Kadi koristab. Staatiline leht Cloudflare Workeri all.
   Ainus dunaamiline osa: eelvaate aadressid ei tohi Google'i indeksisse jouda. */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const vastus = await env.ASSETS.fetch(request);

    if (url.hostname.endsWith(".workers.dev")) {
      const eelvaade = new Response(vastus.body, vastus);
      eelvaade.headers.set("X-Robots-Tag", "noindex, nofollow");
      return eelvaade;
    }

    return vastus;
  }
};
