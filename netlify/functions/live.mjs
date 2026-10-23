// GET /api/live — ¿está transmitiendo el canal de YouTube?
// Variables de entorno (Netlify → Project configuration → Environment variables):
//   YT_API_KEY     clave de YouTube Data API v3
//   YT_CHANNEL_ID  ID del canal (empieza con "UC")
// Costo por consulta: 2 unidades de cuota. Con la caché de 60 s en la CDN
// son ~2,900 unidades al día, dentro de la cuota gratuita de 10,000.

const json = (body) =>
  new Response(JSON.stringify(body), {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=0, must-revalidate",
      "netlify-cdn-cache-control": "public, s-maxage=60, stale-while-revalidate=60",
    },
  });

export default async () => {
  const key = Netlify.env.get("YT_API_KEY");
  const channel = Netlify.env.get("YT_CHANNEL_ID");
  if (!key || !channel) return json({ live: null, upcoming: [], configured: false });

  try {
    const api = "https://www.googleapis.com/youtube/v3";
    const uploads = "UU" + channel.slice(2);
    const pl = await fetch(
      `${api}/playlistItems?part=contentDetails&maxResults=10&playlistId=${uploads}&key=${key}`
    ).then((r) => r.json());
    const ids = (pl.items || []).map((i) => i.contentDetails.videoId).join(",");
    if (!ids) return json({ live: null, upcoming: [], configured: true });

    const vids = await fetch(
      `${api}/videos?part=snippet,liveStreamingDetails&id=${ids}&key=${key}`
    ).then((r) => r.json());
    const items = vids.items || [];

    const liveItem = items.find((v) => v.snippet.liveBroadcastContent === "live");
    const upcoming = items
      .filter((v) => v.snippet.liveBroadcastContent === "upcoming" && v.liveStreamingDetails?.scheduledStartTime)
      .map((v) => ({ id: v.id, title: v.snippet.title, start: v.liveStreamingDetails.scheduledStartTime }))
      .sort((a, b) => a.start.localeCompare(b.start))
      .slice(0, 3);

    return json({
      live: liveItem ? { id: liveItem.id, title: liveItem.snippet.title } : null,
      upcoming,
      configured: true,
    });
  } catch (e) {
    return json({ live: null, upcoming: [], error: true });
  }
};

export const config = { path: "/api/live" };
