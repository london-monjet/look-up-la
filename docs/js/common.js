// Shared helpers used by every page: loading data, colors, labels.
export const DATA_URL = "data/tonight.geojson";
export const INFO_URL = "data/site_info.json";

export const ACCESS_LABELS = {
  public: "Public",
  restricted: "Private / Reservation",
  unknown: "Check access",
  temporary: "Temporarily closed",
};

// Same three colors as the legend: low -> mid -> high.
const STOPS = [[0, [133, 89, 136]], [50, [72, 52, 117]], [100, [20, 24, 82]]];

export function scoreColor(score) {
  const s = Math.min(Math.max(score, 0), 100);
  const [a, b] = s <= 50 ? [STOPS[0], STOPS[1]] : [STOPS[1], STOPS[2]];
  const t = (s - a[0]) / (b[0] - a[0]);
  const rgb = a[1].map((v, i) => Math.round(v + (b[1][i] - v) * t));
  return `rgb(${rgb.join(",")})`;
}

export function timeAgo(iso) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} h ago`;
  return `${Math.round(hours / 24)} days ago`;
}

// Loads tonight's scores and merges in the hand-written info (access, notes, photo).
export async function loadSites() {
  const stamp = Date.now();
  const [dataRes, infoRes] = await Promise.all([
    fetch(`${DATA_URL}?t=${stamp}`, { cache: "no-store" }),
    fetch(`${INFO_URL}?t=${stamp}`, { cache: "no-store" }).catch(() => null),
  ]);
  if (!dataRes.ok) throw new Error(`HTTP ${dataRes.status}`);
  const geojson = await dataRes.json();
  let info = {};
  if (infoRes && infoRes.ok) {
    try { info = await infoRes.json(); } catch { info = {}; }
  }
  return geojson.features.map((f) => {
    const extra = info[f.properties.name] || {};
    return {
      ...f.properties,
      lon: f.geometry.coordinates[0],
      lat: f.geometry.coordinates[1],
      access: ACCESS_LABELS[extra.access] ? extra.access : "unknown",
      notes: extra.notes || "",
      image: extra.image || "",
      website: extra.website || "",
    };
  });
}

export function photoStyle(site) {
  return site.image ? `url("${encodeURI(site.image)}")` : "";
}

export function headerNav(current) {
  const link = (href, text, key) =>
    `<a href="${href}"${current === key ? ' aria-current="page"' : ""}>${text}</a>`;
  return link("index.html#map", "Map", "map") + link("sites.html", "Sites", "sites");
}
