export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/news-sitemap.xml") {
      const upstream = await fetch(env.NEWS_SITEMAP_URL, {
        headers: { "User-Agent": "AlbanyNewsSitemapProxy/1.0" },
      });

      if (!upstream.ok) {
        return new Response("News sitemap unavailable", { status: 502 });
      }

      const body = await upstream.text();
      return new Response(body, {
        status: 200,
        headers: {
          "content-type": "application/xml; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      });
    }

    return fetch(request);
  },
};
