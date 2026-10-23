#!/usr/bin/env python3
"""Votante Latino — sitio bilingüe (es / en).

Uso:  python3 build.py   → genera dist/
Configuración general en site.json; textos en content.json;
datos por estado en data/*.json.
"""
import shutil, json, hashlib, datetime as dt
from email.utils import format_datetime
import markdown, yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
C = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
SITE["v"] = hashlib.md5(b"".join((ROOT / "static" / f).read_bytes() for f in ("site.css", "site.js"))).hexdigest()[:8]


def load_data(name, default):
    f = ROOT / "data" / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


RESULTS = load_data("results_urls.json", {})
CLOSING = load_data("poll_closing.json", {})

STATES = [
 ("al","Alabama","Alabama"),("ak","Alaska","Alaska"),("az","Arizona","Arizona"),
 ("ar","Arkansas","Arkansas"),("ca","California","California"),("co","Colorado","Colorado"),
 ("ct","Connecticut","Connecticut"),("de","Delaware","Delaware"),
 ("dc","Distrito de Columbia","District of Columbia"),("fl","Florida","Florida"),
 ("ga","Georgia","Georgia"),("hi","Hawái","Hawaii"),("id","Idaho","Idaho"),
 ("il","Illinois","Illinois"),("in","Indiana","Indiana"),("ia","Iowa","Iowa"),
 ("ks","Kansas","Kansas"),("ky","Kentucky","Kentucky"),("la","Luisiana","Louisiana"),
 ("me","Maine","Maine"),("md","Maryland","Maryland"),("ma","Massachusetts","Massachusetts"),
 ("mi","Míchigan","Michigan"),("mn","Minnesota","Minnesota"),("ms","Misisipi","Mississippi"),
 ("mo","Misuri","Missouri"),("mt","Montana","Montana"),("ne","Nebraska","Nebraska"),
 ("nv","Nevada","Nevada"),("nh","Nuevo Hampshire","New Hampshire"),
 ("nj","Nueva Jersey","New Jersey"),("nm","Nuevo México","New Mexico"),
 ("ny","Nueva York","New York"),("nc","Carolina del Norte","North Carolina"),
 ("nd","Dakota del Norte","North Dakota"),("oh","Ohio","Ohio"),("ok","Oklahoma","Oklahoma"),
 ("or","Oregón","Oregon"),("pa","Pensilvania","Pennsylvania"),
 ("ri","Rhode Island","Rhode Island"),("sc","Carolina del Sur","South Carolina"),
 ("sd","Dakota del Sur","South Dakota"),("tn","Tennessee","Tennessee"),("tx","Texas","Texas"),
 ("ut","Utah","Utah"),("vt","Vermont","Vermont"),("va","Virginia","Virginia"),
 ("wa","Washington","Washington"),("wv","Virginia Occidental","West Virginia"),
 ("wi","Wisconsin","Wisconsin"),("wy","Wyoming","Wyoming"),
]

PAGES = ["noche-electoral", "como-votar", "tus-derechos", "verifica",
         "tienda", "quienes-somos", "privacidad"]
CATS = ["elecciones-2026", "explicadores"]
TEMPLATE_FOR = {"noche-electoral": "noche.html", "tienda": "tienda.html"}


def load_news():
    """Notas en content/noticias/*.md con encabezado YAML (las crea el panel)."""
    out = {"es": [], "en": []}
    for f in sorted((ROOT / "content" / "noticias").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            continue
        _, head, body = raw.split("---", 2)
        m = yaml.safe_load(head) or {}
        if m.get("draft") or m.get("lang") not in out:
            continue
        d = m["date"]
        if isinstance(d, str):
            d = dt.datetime.fromisoformat(d)
        if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
            d = dt.datetime(d.year, d.month, d.day, 9)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone(dt.timedelta(hours=-5)))
        m["date"] = d
        m["slug"] = f.stem
        m["html"] = markdown.markdown(body.strip(), extensions=["extra", "sane_lists"])
        m["words"] = len(body.split())
        m.setdefault("sources", [])
        out[m["lang"]].append(m)
    for l in out:
        out[l].sort(key=lambda a: a["date"], reverse=True)
    return out


NEWS = load_news()
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


def fecha(d, lang):
    return (f"{d.day} de {MESES[d.month-1]} de {d.year}" if lang == "es"
            else f"{MONTHS[d.month-1]} {d.day}, {d.year}")


env.filters["fecha"] = fecha


def url(lang, page=None):
    pre = "" if lang == "es" else "/en"
    return f"{pre}/{page}/" if page else f"{pre}/"


def out_path(lang, page=None):
    base = DIST if lang == "es" else DIST / "en"
    return (base / page / "index.html") if page else base / "index.html"


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ALL_URLS = []


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    for lang in ("es", "en"):
        t = C[lang]
        other = "en" if lang == "es" else "es"
        names = {c: (es if lang == "es" else en) for c, es, en in STATES}
        states = sorted(names.items(), key=lambda s: s[1])
        results = [(c, n, RESULTS[c]["url"]) for c, n in states
                   if c in RESULTS and RESULTS[c].get("url")]
        closing = [{"et": g["et"] if lang == "en" else g["et"],
                    "names": sorted(names[c] for c in g["states"] if c in names)}
                   for g in CLOSING.get("groups", []) if g.get("states")]
        common = dict(site=SITE, t=t, lang=lang, states=states, pages=PAGES,
                      results=results, closing=closing,
                      url=lambda p=None, l=lang: url(l, p))
        news = NEWS[lang]
        for a in news:
            a["url"] = url(lang, "noticias/" + a["slug"])
        other_by_ref = {a.get("ref"): a for a in NEWS[other] if a.get("ref")}
        common["news"] = news
        p = out_path(lang); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(env.get_template("home.html").render(
            **common, page=None, pg=None, alt=url(other)), encoding="utf-8")
        for page in PAGES:
            p = out_path(lang, page); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(env.get_template(TEMPLATE_FOR.get(page, "page.html")).render(
                **common, page=page, pg=t["pages"][page], alt=url(other, page)),
                encoding="utf-8")

        # Noticias: portada, categorías y notas
        np = t["news"]
        for cat in [None] + CATS:
            sel = [a for a in news if cat is None or a.get("category") == cat]
            path = "noticias" + (f"/{cat}" if cat else "")
            p = out_path(lang, path); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(env.get_template("news_list.html").render(
                **common, page="noticias", cat=cat, items=sel,
                pg={"title": np["cats"][cat] if cat else np["title"], "lede": np["lede"]},
                alt=url(other, path)), encoding="utf-8")
        for a in news:
            tr = other_by_ref.get(a.get("ref"))
            related = [r for r in news if r is not a and r.get("category") == a.get("category")][:3]
            p = out_path(lang, "noticias/" + a["slug"]); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(env.get_template("news_article.html").render(
                **common, page="noticias", a=a, related=related, tr=tr,
                pg={"title": a["title"], "lede": a["dek"]},
                alt=url(other, "noticias/" + tr["slug"]) if tr else url(other, "noticias")),
                encoding="utf-8")
        # RSS
        base = f"https://{SITE['domain']}"
        items = "".join(
            f"<item><title>{esc(a['title'])}</title><link>{base}{a['url']}</link>"
            f"<guid>{base}{a['url']}</guid><pubDate>{format_datetime(a['date'])}</pubDate>"
            f"<description>{esc(a['dek'])}</description></item>" for a in news[:30])
        feed = out_path(lang, "noticias").parent / "rss.xml"
        feed.write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
                        f'<title>Votante Latino — {esc(np["title"])}</title><link>{base}{url(lang, "noticias")}</link>'
                        f'<description>{esc(np["lede"])}</description><language>{t["html_lang"]}</language>'
                        f'{items}</channel></rss>', encoding="utf-8")
        ALL_URLS.extend([url(lang, "noticias")] + [url(lang, "noticias/" + c) for c in CATS] + [a["url"] for a in news])

    shutil.copytree(ROOT / "static", DIST / "static")
    if (ROOT / "admin").exists():
        shutil.copytree(ROOT / "admin", DIST / "admin")
    t = C["es"]
    (DIST / "404.html").write_text(env.get_template("page.html").render(
        site=SITE, t=t, lang="es", url=lambda p=None: url("es", p), states=[],
        pages=PAGES, page="404", alt="/en/",
        pg={"title": "Página no encontrada", "lede": "Esta dirección no existe o cambió.",
            "body": "<p><a href=\"/\">Ir a la portada</a> · <a href=\"/en/\">Go to the English home page</a></p>"}),
        encoding="utf-8")

    urls = [url(l, p) for l in ("es", "en") for p in [None] + PAGES] + ALL_URLS
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>https://{SITE['domain']}{u}</loc></url>\n" for u in urls)
        + "</urlset>\n", encoding="utf-8")
    pre = SITE["prelaunch"]
    (DIST / "robots.txt").write_text(
        ("User-agent: *\nDisallow: /\n" if pre else "User-agent: *\nAllow: /\n")
        + f"Sitemap: https://{SITE['domain']}/sitemap.xml\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  X-Frame-Options: SAMEORIGIN\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
        + ("  X-Robots-Tag: noindex\n" if pre else "")
        + "/static/img/*\n  Cache-Control: public, max-age=86400\n", encoding="utf-8")
    print("✓ dist/ listo:", len(urls), "páginas;", len(NEWS["es"]), "+", len(NEWS["en"]), "notas;",
          len(RESULTS), "enlaces de resultados;", len(CLOSING.get("groups", [])), "grupos de cierre")


if __name__ == "__main__":
    build()
