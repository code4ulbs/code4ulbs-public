#!/usr/bin/env python3
"""Actualizează `contributors` din site/data/projects.json cu datele din GitHub.

Folosire (necesită `gh` autentificat cu drept de citire pe repo-urile organizației):
  python3 site/tools/fetch_contributors.py            # îmbină în projects.json
  python3 site/tools/fetch_contributors.py --print    # doar afișează tabelul, fără să scrie

Reguli:
  - boturile (dependabot, Copilot, cmi-bot ...) sunt ignorate;
  - persoanele deja prezente (după `handle`) își păstrează `name` și `confirmed`;
  - persoanele noi intră cu `confirmed: false`; numele vine din profilul GitHub (dacă e public),
    altfel „<handle> (de completat)”;
  - `site.handle_names` din projects.json mapează handle -> nume real; același nume = aceeași persoană (deduplicat);
  - `handle` nu se afișează niciodată pe site, doar în build-ul `--draft`.
"""
import json
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "projects.json"

# slug-ul aplicației -> repo-urile GitHub din care se adună contributorii
REPOS = {
    "ulbs-connect": ["code4ulbs/ulbs-connect-frontend", "code4ulbs/ulbs-connect-backend"],
    "schedule": ["code4ulbs/schedule"],
    "gradis": ["code4ulbs/gradis", "code4ulbs/gradis-tools"],
    "platacuora": ["code4ulbs/platacuora"],
    "internships": ["code4ulbs/internships"],
    "exams": ["code4ulbs/exams"],
    "teme-licenta": ["code4ulbs/teme_licenta"],
    "adeverinte": ["code4ulbs/adeverinte"],
    "backstage": ["code4ulbs/ulbs-backstage"],
    "ums-proxy": ["code4ulbs/ums-g8"],
    "site-cie": ["ULBS/site_dep_cie"],
}
BOTS = {"copilot", "dependabot", "github-actions", "cmi-bot", "copilot-swe-agent"}


def gh(*args):
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return out.stdout


def repo_contributors(repo):
    raw = gh(f"repos/{repo}/contributors?per_page=100", "--paginate", "--jq",
             '.[] | select(.type=="User") | "\\(.login)\\t\\(.contributions)"')
    if raw is None:
        print(f"  ! nu pot citi {repo}", file=sys.stderr)
        return []
    rows = []
    for line in raw.splitlines():
        login, n = line.split("\t")
        if login.lower() not in BOTS and not login.lower().endswith("[bot]"):
            rows.append((login, int(n)))
    return rows


_names = {}


def profile_name(login):
    if login not in _names:
        raw = gh(f"users/{login}", "--jq", ".name // \"\"")
        _names[login] = (raw or "").strip()
    return _names[login]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    projects = {p["slug"]: p for p in data["projects"] + data["support"]}
    aliases = data["site"].get("handle_names", {})  # handle GitHub -> nume real (completat manual)
    for slug, repos in REPOS.items():
        project = projects.get(slug)
        if not project:
            continue
        commits = {}
        for repo in repos:
            for login, n in repo_contributors(repo):
                commits[login] = commits.get(login, 0) + n
        existing = {c.get("handle"): c for c in project.get("contributors", []) if c.get("handle")}
        manual = [c for c in project.get("contributors", []) if not c.get("handle")]
        merged, seen = [], set()
        for login, _ in sorted(commits.items(), key=lambda kv: -kv[1]):
            if login in existing:
                entry = existing[login]
            else:
                name = aliases.get(login) or profile_name(login) or f"{login} (de completat)"
                entry = {"name": name, "handle": login, "confirmed": False}
            key = entry["name"].lower()
            if not key.endswith("(de completat)"):
                if key in seen:  # aceeași persoană cu două conturi GitHub
                    continue
                seen.add(key)
            merged.append(entry)
        project["contributors"] = manual + merged
        print(f"{slug}: {len(merged)} din GitHub, {len(manual)} adăugați manual")
        if "--print" in sys.argv:
            for c in merged:
                print(f"    {c['handle']:<22} {c['name']}  {'[confirmat]' if c.get('confirmed') else ''}")
    if "--print" not in sys.argv:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Scris: {DATA}")


if __name__ == "__main__":
    main()
