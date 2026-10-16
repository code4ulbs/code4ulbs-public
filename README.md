# code4ulbs.github.io

Pagina de portofoliu [Code4ULBS](https://github.com/code4ulbs): https://code4ulbs.github.io/

- Datele sunt în [`site/data/projects.json`](site/data/projects.json) (sursa unică de adevăr)
- Generare locală: `python3 site/build.py --draft` (arată și persoanele neconfirmate), apoi deschide `site/dist/index.html`
- Persoanele cu `"confirmed": false` nu apar în build-ul de producție; build-ul eșuează dacă ar apărea
- Publicare: automat, prin GitHub Actions, la push pe `main` (Settings → Pages → Source = GitHub Actions)
