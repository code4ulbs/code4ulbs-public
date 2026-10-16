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
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DRAFT = "--draft" in sys.argv
MERMAID = "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"

STATUS = {
    "production": ("În producție", "ok"),
    "staging": ("Staging", "warn"),
    "development": ("În dezvoltare", "info"),
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
    <nav><a href="{root}index.html#proiecte">Proiecte</a><a href="{root}index.html#standarde">Standarde</a><a href="{root}index.html#responsabili">Responsabili</a><a href="{root}index.html#implica-te">Implică-te</a></nav>
  </div>
</header>
{body}
<footer class="foot"><div class="wrap">Code4ULBS · Universitatea „Lucian Blaga” din Sibiu · în colaborare cu Sibiu IT Cluster</div></footer>
<script src="{MERMAID}"></script>
<script>
mermaid.initialize({{startOnLoad: true, theme: "base", themeVariables: {{
  fontFamily: "Open Sans, sans-serif", primaryColor: "#D7E1EB", primaryTextColor: "#011F5B",
  primaryBorderColor: "#0B2F63", lineColor: "#454B67", secondaryColor: "#F7F7F7"}}}});
</script>
</body>
</html>
"""


def mermaid(lines):
    return '<pre class="mermaid">' + e("\n".join(l.replace("\\n", "<br/>") for l in lines)) + "</pre>"


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
  <div class="card-top"><h3>{e(p['name'])}</h3>{status_badge(p['status'])}</div>
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
        f"<tr><td><a href='projects/{p['slug']}.html'>{e(p['name'])}</a></td>"
        f"<td>{people_cell(p)}</td></tr>"
        for p in data["projects"] + data["support"]
    )
    body = f"""
<section class="hero"><div class="wrap">
  <img class="hero-logo" src="assets/logos/code4ulbs_dark_background.svg" alt="Code4ULBS" height="64">
  <h1>Portofoliul Code4ULBS</h1>
  <p class="lead">{e(s['tagline'])}</p>
</div></section>
<main class="wrap">
  <section><h2>Despre inițiativă</h2><p>{e(s['about'])}</p></section>
  <section id="proiecte"><h2>Aplicații</h2><div class="grid">{cards}</div>
    <h3 class="sub">Infrastructură și suport</h3><div class="grid">{support}</div></section>
  <section id="peisaj"><h2>Cum se leagă aplicațiile</h2>
    <p>Peisajul aplicațiilor: ce rulează în infrastructura ULBS și ce este în afara ei, ce aplicații au bază de date și de ce tip, cum se autentifică utilizatorii (Google Workspace) și de unde vin datele universitare (UMS prin proxy, orarul din Schedule).</p>
    <div class="diagram"><a href="assets/diagrams/landscape.svg" target="_blank" rel="noopener" title="Deschide diagrama mărită"><img src="assets/diagrams/landscape.svg" alt="Diagrama peisajului aplicațiilor Code4ULBS: aplicații, baze de date, autentificare Google, UMS proxy și sisteme externe" width="1929" height="1212"></a></div>
    <p class="muted">Diagrama este generată din cod PlantUML: <a href="{e(s['repo_url'])}/blob/main/site/diagrams/landscape.puml">landscape.puml</a>. Click pe imagine pentru varianta mărită.</p></section>
  <section id="standarde"><h2>Standarde Code4ULBS</h2><p>Fiecare proiect respectă aceleași reguli, descrise în <a href="{e(s['starter_url'])}">code4ulbs-starter</a>.</p><div class="grid tiles">{stds}</div></section>
  <section><h2>Infrastructură</h2><div class="grid tiles">{infra}</div></section>
  <section id="responsabili"><h2>Cine răspunde de ce</h2>
    <div class="table-wrap"><table><thead><tr><th>Aplicație</th><th>Responsabili</th></tr></thead><tbody>{rows}</tbody></table></div></section>
  <section id="implica-te"><h2>Implică-te</h2>
    <p>Începe cu <a href="{e(s['starter_url'])}">code4ulbs-starter</a>: cerințe, standarde de dezvoltare și ghiduri de contribuție. Echipele comunică pe Discord, iar fiecare modificare pornește de la un issue. Mai multe informații pe <a href="{e(s['cie_url'])}">pagina Code4ULBS a Departamentului CIE</a>.</p></section>
</main>"""
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
    for r in p.get("repos", []):
        priv = " (privat)" if r.get("private") else ""
        links.append(f'<span class="chip">repo: code4ulbs/{e(r["name"])}{priv}</span>')
    head = f"""<section class="hero small"><div class="wrap">
  <p class="crumb"><a href="../index.html#proiecte">← Toate proiectele</a></p>
  <h1>{e(p['name'])}</h1><p class="lead">{e(p['tagline'])}</p>
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
    if p.get("arch"):
        note = f"<p>{md(p['arch_note'])}</p>" if p.get("arch_note") else ""
        sec.append(f"<section><h2>Arhitectură</h2>{mermaid(p['arch'])}{note}</section>")
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
    return page(f"{p['name']} — Code4ULBS", head + '<main class="wrap">' + "".join(sec) + "</main>", root)


def check_no_unconfirmed(data):
    """Garda: în build de producție nu apare nicio persoană neconfirmată.

    - pe pagina unui proiect nu are voie să apară numele unei persoane neconfirmate pentru acel proiect
      (decât dacă persoana e confirmată pe același proiect);
    - pe pagina principală nu apar nume care nu sunt confirmate nicăieri.
    """
    if DRAFT:
        return
    projects = data["projects"] + data["support"]
    confirmed_all = {x["name"] for p in projects for x in p.get("people", []) if x.get("confirmed")}
    unconfirmed_all = {x["name"] for p in projects for x in p.get("people", []) if not x.get("confirmed")}
    index = (DIST / "index.html").read_text(encoding="utf-8")
    for name in unconfirmed_all - confirmed_all:
        if name in index:
            sys.exit(f"EROARE: persoana neconfirmată „{name}” apare în index.html")
    for p in projects:
        ok = {x["name"] for x in p.get("people", []) if x.get("confirmed")}
        txt = (DIST / "projects" / f"{p['slug']}.html").read_text(encoding="utf-8")
        for x in p.get("people", []):
            if not x.get("confirmed") and x["name"] not in ok and x["name"] in txt:
                sys.exit(f"EROARE: persoana neconfirmată „{x['name']}” apare în projects/{p['slug']}.html")


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
