#!/usr/bin/env python3
"""Generează site-ul de portofoliu Code4ULBS din data/projects.json.

Folosire:
  python3 site/build.py            # build de producție (omite persoanele neconfirmate)
  python3 site/build.py --draft    # arată și persoanele neconfirmate, evidențiat
Rezultatul apare în site/dist/ (nu se comite).
"""
import html
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DRAFT = "--draft" in sys.argv

STATUS = {
    "production": ("În producție", "ok"),
    "staging": ("Staging", "warn"),
    "development": ("În dezvoltare", "info"),
    "deprecated": ("Deprecated", "muted"),
}
ROLE = {"responsabil": "Responsabil", "coordonator": "Coordonator (cadru didactic ULBS)", "tech-lead": "Tech lead"}


def e(text):
    return html.escape(str(text), quote=True)


def md(text):
    """Escape + `cod` inline."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(text))


def ul(items):
    return "<ul>" + "".join(f"<li>{md(i)}</li>" for i in items) + "</ul>"


def people(project):
    """Persoanele afișabile. În producție doar cele confirmate."""
    return [p for p in project.get("people", []) if DRAFT or p.get("confirmed")]


def sort_key(name):
    base = unicodedata.normalize("NFD", name.casefold())
    return "".join(ch for ch in base if not unicodedata.combining(ch))


def contributors(project):
    """Contributorii afișabili. În producție: cei confirmați sau confirmați ca responsabili pe același proiect."""
    ok_people = {x["name"] for x in project.get("people", []) if x.get("confirmed")}
    shown = [c for c in project.get("contributors", []) if DRAFT or c.get("confirmed") or c["name"] in ok_people]
    return sorted(shown, key=lambda c: sort_key(c["name"]))


def total_contributors(projects):
    """Numărul de persoane distincte din toate listele (fără a dezvălui nume)."""
    seen = set()
    for p in projects:
        for c in p.get("contributors", []):
            name = c["name"]
            seen.add(c.get("handle", name).lower() if name.endswith("(de completat)") else sort_key(name))
    return len(seen)


def partner_logo(pid, partners, root):
    pt = partners[pid]
    img = f'<img src="{root}assets/partners/{e(pt["logo"])}" alt="{e(pt["name"])}" loading="lazy">'
    if pt.get("url"):
        return f'<a class="logo" href="{e(pt["url"])}" title="{e(pt["name"])}" target="_blank" rel="noopener">{img}</a>'
    return f'<span class="logo" title="{e(pt["name"])}">{img}</span>'


def pname(project):
    """Numele proiectului; tăiat (strike-through) dacă e deprecated."""
    name = e(project["name"])
    return f'<s class="deprecated">{name}</s>' if project.get("status") == "deprecated" else name


def status_badge(status):
    label, cls = STATUS[status]
    return f'<span class="badge {cls}">{label}</span>'


def page(title, body, root, extra_head=""):
    return f"""<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="icon" href="{root}assets/logos/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
{extra_head}
</head>
<body>
<header class="nav">
  <div class="wrap nav-in">
    <a class="brand" href="{root}index.html" aria-label="Code4ULBS — pagina principală">
      <img src="{root}assets/logos/LOGO-ULBS_orizontal_negativ.png" alt="Universitatea Lucian Blaga din Sibiu" height="34">
      <span class="brand-sep"></span><span class="brand-name">Code4ULBS</span>
    </a>
    <nav><a href="{root}index.html#povestea">Povestea</a><a href="{root}index.html#proiecte">Proiecte</a><a href="{root}index.html#parteneri">Parteneri</a><a href="{root}index.html#standarde">Cum lucrăm</a><a href="{root}index.html#responsabili">Responsabili</a><a href="{root}index.html#implica-te">Devino voluntar</a></nav>
  </div>
</header>
{body}
<footer class="foot"><div class="wrap">Code4ULBS · Universitatea „Lucian Blaga” din Sibiu · în colaborare cu Sibiu IT Cluster · <a href="{root}index.html#implica-te">Devino voluntar</a></div></footer>
</body>
</html>
"""


def svg_size(path):
    """Dimensiunile (px) ale unui SVG generat de PlantUML."""
    m = re.search(r'width="(\d+)px" height="(\d+)px"', path.read_text(encoding="utf-8")[:600])
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def people_cell(project):
    found = people(project)
    if not found:
        return '<span class="muted">în curs de completare</span>'
    out = []
    for p in found:
        role = "" if p["role"] == "responsabil" else f" <span class='muted'>({ROLE[p['role']]})</span>"
        mark = ' <span class="badge draft">neconfirmat</span>' if not p.get("confirmed") else ""
        out.append(f"{e(p['name'])}{role}{mark}")
    return "<br>".join(out)


def stack_groups(p):
    """Stack ca dicționar de grupe; o listă simplă devine o singură grupă."""
    st = p.get("stack", {})
    return st if isinstance(st, dict) else {"Tehnologii": st}


def card(p, root):
    stack = []
    for name, group in stack_groups(p).items():
        if name not in ("Calitate", "Infrastructură", "OMR"):
            stack.extend(group[:2])
    chips = "".join(f'<span class="chip">{e(s)}</span>' for s in stack[:5])
    return f"""<a class="card" href="{root}projects/{p['slug']}.html">
  <div class="card-top"><h3>{pname(p)}</h3>{status_badge(p['status'])}</div>
  <p>{e(p['tagline'])}</p>
  <div class="chips">{chips}</div>
</a>"""


def build_index(data):
    s = data["site"]
    cards = "".join(card(p, "") for p in data["projects"])
    support = "".join(card(p, "") for p in data["support"])
    stds = "".join(f"<div class='tile'><h3>{e(x['title'])}</h3><p>{e(x['text'])}</p></div>" for x in data["standards"])
    infra = "".join(f"<div class='tile'><h3>{e(x['title'])}</h3><p>{e(x['text'])}</p></div>" for x in data["infra"])
    rows = "".join(
        f"<tr><td><a href='projects/{p['slug']}.html'>{pname(p)}</a></td>"
        f"<td>{people_cell(p)}</td></tr>"
        for p in data["projects"] + data["support"]
    )
    projects = data["projects"] + data["support"]
    partners = s["partners"]
    why = "".join(f"<div class='tile'><h3>{e(x['title'])}</h3><p>{e(x['text'])}</p></div>" for x in s["story"]["why"])
    steps = "".join(f"<li><span class='when'>{e(t['when'])}</span><p>{e(t['text'])}</p></li>" for t in s["timeline"])
    stats = [
        (str(len(data["projects"])), "aplicații"),
        (str(total_contributors(projects)), "contributori"),
        (str(s.get("faculties", 9)), "facultăți deservite"),
    ]
    if s.get("users_connect"):
        stats.append((s["users_connect"], "utilizatori în ULBS Connect"))
    stat_html = "".join(f"<div class='stat'><strong>{e(n)}</strong><span>{e(l)}</span></div>" for n, l in stats)
    org_logos = "".join(partner_logo(k, partners, "") for k, v in partners.items() if v["group"] == "organizers")
    con_logos = "".join(partner_logo(k, partners, "") for k, v in partners.items() if v["group"] == "contributors")
    pillars = "".join(
        f"<div class='tile'><h3>{e(w['title'])}</h3>{ul(w['items'])}</div>" for w in s["workflow"]
    )
    lessons = "".join(f"<li>{e(x)}</li>" for x in s["lessons"])
    cta = s["cta"]
    roles = "".join(f"<span class='chip'>{e(r)}</span>" for r in cta["people"]["roles"])
    body = f"""
<section class="hero"><div class="wrap">
  <img class="hero-logo" src="assets/logos/code4ulbs_dark_background.svg" alt="Code4ULBS" height="64">
  <h1>Portofoliul Code4ULBS</h1>
  <p class="lead">{e(s['tagline'])}</p>
  <p class="hero-cta"><a class="btn" href="#proiecte">Vezi aplicațiile</a> <a class="btn ghost" href="{e(cta['form_url'])}" target="_blank" rel="noopener">Devino voluntar</a></p>
</div></section>
<div class="stats"><div class="wrap stats-in">{stat_html}</div></div>
<main class="wrap">
  <section id="povestea"><h2>Povestea Code4ULBS</h2>
    <p>{e(s['story']['intro'])}</p>
    <h3 class="sub">De ce am pornit</h3><div class="grid tiles">{why}</div>
    <h3 class="sub">Istoricul, pe scurt</h3><ol class="timeline">{steps}</ol></section>
  <section id="proiecte"><h2>Aplicații</h2><div class="grid">{cards}</div>
    <h3 class="sub">Infrastructură și suport</h3><div class="grid">{support}</div></section>
</main>
<section class="band" id="parteneri"><div class="wrap">
  <h2>Parteneri și susținători</h2>
  <p class="band-lead">Code4ULBS este o inițiativă a Sibiu IT Cluster și a Universității „Lucian Blaga” din Sibiu. Mulțumim companiilor și structurilor care au contribuit la proiecte.</p>
  <div class="logos">{org_logos}</div>
  <div class="logos small">{con_logos}</div>
</div></section>
<main class="wrap">
  <section id="peisaj"><h2>Cum se leagă aplicațiile</h2>
    <p>Peisajul aplicațiilor: ce rulează în infrastructura ULBS și ce este în afara ei, ce aplicații au bază de date și de ce tip, cum se autentifică utilizatorii (Google Workspace) și de unde vin datele universitare (UMS prin proxy, orarul din Schedule).</p>
    <div class="diagram"><a href="assets/diagrams/landscape.svg" target="_blank" rel="noopener" title="Deschide diagrama mărită"><img src="assets/diagrams/landscape.svg" alt="Diagrama peisajului aplicațiilor Code4ULBS: aplicații, baze de date, autentificare Google, UMS proxy și sisteme externe" width="1929" height="1212"></a></div>
    <p class="muted">Diagrama este generată din cod PlantUML: <a href="{e(s['repo_url'])}/blob/main/site/diagrams/landscape.puml">landscape.puml</a>. Click pe imagine pentru varianta mărită.</p></section>
  <section id="standarde"><h2>Cum lucrăm</h2>
    <p>Lucrăm pe GitHub, cu aceleași reguli pentru toate proiectele, descrise în <a href="{e(s['starter_url'])}">code4ulbs-starter</a>. Folosim și GitHub Copilot, de la implementare până la deployment.</p>
    <div class="grid tiles">{pillars}</div>
    <div class="diagram flow"><a href="assets/diagrams/workflow.svg" target="_blank" rel="noopener" title="Deschide diagrama mărită"><img src="assets/diagrams/workflow.svg" alt="Fluxul de lucru: issue, AI coding agent, code review și testare, merge, deployment, testare" width="1581" height="253"></a></div>
    <p class="muted">Diagrama: <a href="{e(s['repo_url'])}/blob/main/site/diagrams/workflow.puml">workflow.puml</a>.</p>
    <h3 class="sub">Standarde Code4ULBS</h3><div class="grid tiles">{stds}</div></section>
  <section><h2>Infrastructură</h2><div class="grid tiles">{infra}</div></section>
  <section id="lectii"><h2>Ce am învățat</h2><ul>{lessons}</ul>
    <p class="muted">Și am descoperit că: comunitatea IT din Sibiu este plină de oameni extraordinari.</p></section>
  <section id="responsabili"><h2>Cine răspunde de ce</h2>
    <div class="table-wrap"><table><thead><tr><th>Aplicație</th><th>Responsabili</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main>
<section class="band cta" id="implica-te"><div class="wrap">
  <h2>{e(cta['title'])}</h2>
  <div class="grid cta-grid">
    <div class="tile"><h3>{e(cta['people']['title'])}</h3><div class="chips">{roles}</div><p>{e(cta['people']['text'])}</p></div>
    <div class="tile"><h3>{e(cta['orgs']['title'])}</h3><p>{e(cta['orgs']['text'])}</p></div>
  </div>
  <p class="band-lead">{e(cta['reward'])}</p>
  <p><a class="btn big" href="{e(cta['form_url'])}" target="_blank" rel="noopener">Devino voluntar</a>
  <a class="btn ghost" href="{e(s['starter_url'])}">Ghidul contributorilor</a>
  <a class="btn ghost" href="{e(s['cie_url'])}">Pagina Code4ULBS la CIE</a></p>
</div></section>"""
    return page(s["title"], body, "")


def build_project(p, data):
    root = "../"
    sec = []
    meta = [status_badge(p["status"])]
    if p.get("version"):
        meta.append(f'<span class="chip">v{e(p["version"])}</span>')
    links = []
    if p.get("url"):
        links.append(f'<a class="btn" href="{e(p["url"])}">Deschide aplicația</a>')
    if p.get("staging_url"):
        links.append(f'<a class="btn ghost" href="{e(p["staging_url"])}">Staging</a>')
    for r in p.get("repos", []):
        priv = " (privat)" if r.get("private") else ""
        links.append(f'<span class="chip">repo: code4ulbs/{e(r["name"])}{priv}</span>')
    head = f"""<section class="hero small"><div class="wrap">
  <p class="crumb"><a href="../index.html#proiecte">← Toate proiectele</a></p>
  <h1>{pname(p)}</h1><p class="lead">{e(p['tagline'])}</p>
  <div class="meta">{''.join(meta)}</div><div class="meta">{''.join(links)}</div>
</div></section>"""
    sec.append(f"<section><h2>Descriere</h2><p>{md(p['description'])}</p></section>")
    if p.get("features"):
        sec.append(f"<section><h2>Funcționalități cheie</h2>{ul(p['features'])}</section>")
    shots = p.get("screenshots", [])
    if shots:
        figs = "".join(
            f'<figure><a href="{root}assets/screenshots/{p["slug"]}/{e(s["file"])}"><img loading="lazy" src="{root}assets/screenshots/{p["slug"]}/{e(s["file"])}" alt="{e(s["caption"])}"></a><figcaption>{e(s["caption"])}</figcaption></figure>'
            for s in shots
        )
        sec.append(f'<section><h2>Screenshots</h2><div class="shots">{figs}</div></section>')
    else:
        sec.append('<section><h2>Screenshots</h2><div class="placeholder">Capturile de ecran se adaugă în curând.</div></section>')
    if p.get("stack"):
        groups = "".join(
            f"<div class='tile'><h3>{e(k)}</h3><div class='chips'>" + "".join(f"<span class='chip'>{e(v)}</span>" for v in vals) + "</div></div>"
            for k, vals in stack_groups(p).items()
        )
        sec.append(f"<section><h2>Tehnologii</h2><div class='grid tiles'>{groups}</div></section>")
    if p.get("arch_diagram"):
        name = p["arch_diagram"]
        w, h = svg_size(ROOT / "assets" / "diagrams" / f"{name}.svg")
        size = f' width="{w}" height="{h}"' if w else ""
        note = f"<p>{md(p['arch_note'])}</p>" if p.get("arch_note") else ""
        sec.append(
            f'<section><h2>Arhitectură</h2><div class="diagram app"><a href="{root}assets/diagrams/{name}.svg" target="_blank" rel="noopener" title="Deschide diagrama mărită">'
            f'<img src="{root}assets/diagrams/{name}.svg" alt="Diagrama de arhitectură {e(p["name"])}"{size}></a></div>{note}'
            f'<p class="muted">Diagrama este generată din cod PlantUML: <a href="{e(data["site"]["repo_url"])}/blob/main/site/diagrams/{name}.puml">{name}.puml</a>.</p></section>'
        )
    if p.get("deployment"):
        sec.append(f"<section><h2>Deployment</h2>{ul(p['deployment'])}</section>")
    extras = []
    if p.get("roles"):
        extras.append(f"<div class='tile'><h3>Roluri și utilizatori</h3>{ul(p['roles'])}</div>")
    if p.get("integrations"):
        extras.append(f"<div class='tile'><h3>Integrări</h3>{ul(p['integrations'])}</div>")
    if p.get("auth"):
        extras.append(f"<div class='tile'><h3>Autentificare și securitate</h3><p>{md(p['auth'])}</p></div>")
    if p.get("quality"):
        extras.append(f"<div class='tile'><h3>Calitate și testare</h3>{ul(p['quality'])}</div>")
    if extras:
        sec.append(f"<section><h2>Detalii</h2><div class='grid tiles'>{''.join(extras)}</div></section>")
    if p.get("run_local"):
        sec.append(f"<section><h2>Cum rulezi local</h2>{ul(p['run_local'])}</section>")
    if p.get("partners"):
        logos = "".join(partner_logo(k, data["site"]["partners"], root) for k in p["partners"])
        sec.append(f'<section><h2>Susținut de</h2><div class="band mini"><div class="logos small">{logos}</div></div></section>')
    ppl = people(p)
    if ppl:
        items = "".join(
            f"<li><strong>{e(x['name'])}</strong> — {ROLE[x['role']]}"
            + ("" if x.get("confirmed") else f" <span class='badge draft'>neconfirmat · {e(x.get('draft_source', ''))}</span>")
            + "</li>"
            for x in ppl
        )
        sec.append(f"<section><h2>Responsabili</h2><ul>{items}</ul></section>")
    else:
        sec.append("<section><h2>Responsabili</h2><p class='muted'>Responsabilii se completează în curând.</p></section>")
    cons = contributors(p)
    if cons:
        chips = "".join(
            f"<li>{e(c['name'])}"
            + ("" if c.get("confirmed") or not DRAFT else f" <span class='badge draft'>neconfirmat · {e(c.get('handle', ''))}</span>")
            + "</li>"
            for c in cons
        )
        sec.append(f"<section><h2>Contributori</h2><p>Mulțumim tuturor celor care au contribuit la {pname(p)}.</p><ul class='contributors'>{chips}</ul></section>")
    else:
        sec.append("<section><h2>Contributori</h2><p class='muted'>Lista contributorilor se completează în curând.</p></section>")
    return page(f"{p['name']} — Code4ULBS", head + '<main class="wrap">' + "".join(sec) + "</main>", root)


def check_no_unconfirmed(data):
    """Garda: în build de producție nu apare nicio persoană neconfirmată.

    Se verifică responsabilii ȘI contributorii:
    - pe pagina unui proiect nu are voie să apară numele (sau handle-ul) unei persoane neconfirmate pentru acel
      proiect, decât dacă persoana e confirmată pe același proiect;
    - pe pagina principală nu apar nume care nu sunt confirmate nicăieri.
    """
    if DRAFT:
        return
    projects = data["projects"] + data["support"]

    def entries(p):
        return list(p.get("people", [])) + list(p.get("contributors", []))

    def tokens(x):
        out = [x["name"]] + ([x["handle"]] if x.get("handle") else [])
        return [t for t in out if len(t) >= 4 and not t.endswith("(de completat)")]

    def found(token, text):
        return re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text) is not None

    confirmed_all = {x["name"] for p in projects for x in entries(p) if x.get("confirmed")}
    index = (DIST / "index.html").read_text(encoding="utf-8")
    for p in projects:
        for x in entries(p):
            if x.get("confirmed") or x["name"] in confirmed_all:
                continue
            for t in tokens(x):
                if found(t, index):
                    sys.exit(f"EROARE: „{t}” (neconfirmat) apare în index.html")
    for p in projects:
        ok = {x["name"] for x in entries(p) if x.get("confirmed")}
        txt = (DIST / "projects" / f"{p['slug']}.html").read_text(encoding="utf-8")
        for x in entries(p):
            if x.get("confirmed") or x["name"] in ok:
                continue
            for t in tokens(x):
                if found(t, txt):
                    sys.exit(f"EROARE: „{t}” (neconfirmat) apare în projects/{p['slug']}.html")


def main():
    data = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "projects").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", DIST / "assets")
    (DIST / ".nojekyll").write_text("")
    (DIST / "index.html").write_text(build_index(data), encoding="utf-8")
    for p in data["projects"] + data["support"]:
        (DIST / "projects" / f"{p['slug']}.html").write_text(build_project(p, data), encoding="utf-8")
    check_no_unconfirmed(data)
    mode = "DRAFT" if DRAFT else "producție"
    print(f"OK ({mode}): {len(data['projects']) + len(data['support'])} proiecte → {DIST}")


if __name__ == "__main__":
    main()
