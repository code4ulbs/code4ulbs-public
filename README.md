# code4ulbs.github.io

Pagina de portofoliu [Code4ULBS](https://github.com/code4ulbs): https://code4ulbs.github.io/

- Datele sunt în [`site/data/projects.json`](site/data/projects.json) (sursa unică de adevăr)
- Generare locală: `python3 site/build.py --draft` (arată și persoanele neconfirmate), apoi deschide `site/dist/index.html`
- Persoanele cu `"confirmed": false` nu apar în build-ul de producție; build-ul eșuează dacă ar apărea
- Publicare: automat, prin GitHub Actions, la push pe `main` (Settings → Pages → Source = GitHub Actions)

## Diagrame (toate în PlantUML)
`landscape.puml` (peisajul aplicațiilor), `workflow.puml` (cum lucrăm) și `arch-<aplicație>.puml` (arhitectura fiecărei aplicații), cu stilul comun din `_style.iuml`.

### Cum se leagă aplicațiile
- Sursa este [`site/diagrams/landscape.puml`](site/diagrams/landscape.puml) (PlantUML, motor ELK, fără Graphviz).
- După orice modificare: `site/diagrams/render.sh` (necesită Java 17+; descarcă singur PlantUML 1.2026.8), apoi comite și `site/assets/diagrams/landscape.svg`.
- Aplicație nouă: copiază un `arch-*.puml` existent și leagă-l în `landscape.puml`; sau copiază un bloc `rectangle ... <<prod>>` (sau `<<dev>>`) + `database`, apoi leagă-l de Google, UMS proxy, Schedule etc.

## Contributori, parteneri și conținut din prezentări
- `site/data/projects.json`: `contributors` (per aplicație), `site.partners` (logo-uri în `site/assets/partners/`), `site.story`, `site.timeline`, `site.lessons`, `site.cta`.
- Contributorii se actualizează din GitHub cu `python3 site/tools/fetch_contributors.py` (păstrează intrările deja confirmate). `site.handle_names` mapează handle GitHub → nume real.
- În producție apar doar persoanele cu `"confirmed": true` (sau confirmate ca responsabil pe același proiect); `python3 site/build.py` eșuează dacă un nume neconfirmat ar apărea pe site.
