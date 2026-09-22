# Deploying Jakeala Naturals

Two pieces go live, and they live in different places:

| Piece | Folder | Host | Example URL |
| --- | --- | --- | --- |
| **API** (Django + DRF) | `backend/` | **PythonAnywhere** | `https://YOURNAME.pythonanywhere.com/api/` |
| **Website** (Next.js) | `frontend/` | **Vercel** (recommended) | `https://jakeala.com` |

Both pull from the same GitHub repo, so **the workflow is always: push to GitHub → pull on the server.**

```
GitHub (Ikolawole2020/Jakeala_Naturals)
        |
        +--> PythonAnywhere  (git pull  -> migrate -> collectstatic -> Reload)
        |
        +--> Vercel          (auto-deploys on every push, no manual step)
```

> **Read the whole page once before starting.** You will need three things before
> you begin: your PythonAnywhere username, your Vercel account, and a GitHub
> Personal Access Token (only if the repo stays private — see step 1.3).

---

## Part 1 — Backend on PythonAnywhere

### 1.1 Create the account and the web app

1. Sign up at <https://www.pythonanywhere.com> (the free "Beginner" plan is fine).
   Your site will be reachable at `https://YOURNAME.pythonanywhere.com`.
2. Go to the **Web** tab → **Add a new web app**.
3. Choose **Manual configuration** — *not* the "Django" option. That option is
   only for creating brand-new projects and will not use your code.
4. Choose the same Python version you are about to create the virtualenv with.
   (Run `ls /usr/bin/python3.*` in a console to see what is available.
   Python **3.10** is a safe choice — Django 5 needs 3.10+.)

### 1.2 Open a Bash console

**Consoles** tab → **Bash**. Everything below happens in that console.

### 1.3 Clone the repository

Git cannot clone a single subfolder, but **sparse-checkout** downloads only
`backend/` (plus the root-level docs), which is all this server needs:

```bash
cd ~
git clone --filter=blob:none --sparse https://github.com/Ikolawole2020/Jakeala_Naturals.git
cd Jakeala_Naturals
git sparse-checkout set backend
```

Result: `~/Jakeala_Naturals/backend/` exists and `frontend/` does not. Future
`git pull`s respect the sparse setting, so updates stay backend-only.

If your git version is too old for `--sparse`, fall back to a normal clone — the
repo is only a few thousand lines of text, and you can delete the unwanted folder:

```bash
cd ~
git clone https://github.com/Ikolawole2020/Jakeala_Naturals.git
rm -rf ~/Jakeala_Naturals/frontend     # optional: it is unused on this server
```

> `github.com` is on PythonAnywhere's outbound whitelist for free accounts, so the
> clone works without a paid plan.

> **If you make the repo private later**, clone with a GitHub Personal Access
> Token instead (GitHub → *Settings → Developer settings → Personal access tokens*
> → give it read-only **Contents** access to this repo), and store it so pulls do
> not prompt:
>
> ```bash
> git clone https://YOUR_GITHUB_USERNAME:YOUR_TOKEN@github.com/Ikolawole2020/Jakeala_Naturals.git
> cd ~/Jakeala_Naturals
> git remote set-url origin https://YOUR_GITHUB_USERNAME:YOUR_TOKEN@github.com/Ikolawole2020/Jakeala_Naturals.git
> ```
>
> The token is then stored in `.git/config` — keep that account secure.

### 1.4 Create the virtualenv and install dependencies

```bash
mkvirtualenv --python=/usr/bin/python3.10 jakeala-venv
cd ~/Jakeala_Naturals/backend
pip install -r requirements.txt
```

If `mkvirtualenv` is not found, run `source ~/.bashrc` and try again.
Installing Django takes a couple of minutes — that is normal.

### 1.5 Create the production environment file

Copy the template and edit it:

```bash
cd ~/Jakeala_Naturals/backend
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"   # copy this key
nano .env
```

Set the values to:

```ini
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<paste the long random string you just generated>
ALLOWED_HOSTS=YOURNAME.pythonanywhere.com
CORS_ALLOWED_ORIGINS=https://jakeala.com,https://www.jakeala.com
CSRF_TRUSTED_ORIGINS=https://YOURNAME.pythonanywhere.com
DJANGO_SECURE_SSL_REDIRECT=0
```

Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

Notes:

- Replace `YOURNAME` with your real PythonAnywhere username.
- `CORS_ALLOWED_ORIGINS` is the list of **front-end** origins allowed to call the
  API. You will add your Vercel URL here in step 2.4.
- Keep `DJANGO_SECURE_SSL_REDIRECT=0` for now; switch it to `1` in step 3 once
  everything is confirmed working.
- `settings.py` deliberately **refuses to start** if `DJANGO_DEBUG=0` and the
  secret key is still the placeholder — that guard stops an insecure deploy.

### 1.6 Create the database and the admin user

```bash
python manage.py migrate
python manage.py seed
python manage.py collectstatic --noinput
```

`seed` creates the catalogue, the wellness articles and the staff account
(`admin` / `jakeala2026`). **Change that password** — see step 3.4.

### 1.7 Point the web app at your code

Back in the **Web** tab:

1. **Virtualenv** → enter `jakeala-venv` and click OK. It expands to
   `/home/YOURNAME/.virtualenvs/jakeala-venv`.
2. **Source code** → `/home/YOURNAME/Jakeala_Naturals`
3. **Working directory** → `/home/YOURNAME/Jakeala_Naturals/backend`

### 1.8 Paste the WSGI file

PythonAnywhere **ignores** `backend/config/wsgi.py`. You must edit *their* file.

1. In the **Web** tab, click the **WSGI configuration file** link — it opens a path
   like `/var/www/YOURNAME_pythonanywhere_com_wsgi.py`.
2. Select everything in it and delete it.
3. Fill it with the contents of `backend/pythonanywhere_wsgi.py`. **There is
   nothing to edit** — the file resolves your home directory at runtime with
   `os.path.expanduser("~")`, so your username never has to be typed in.
4. Save.

The easiest way to get the text exactly right is to print it in a Bash console and
copy from there, so nothing is mistyped:

```bash
cat ~/Jakeala_Naturals/backend/pythonanywhere_wsgi.py
```

The file only needs three things: your project path on `sys.path`, the
`DJANGO_SETTINGS_MODULE` variable, and the `application` object. All secrets are
read from `backend/.env`, so your console and the web worker stay in sync.


### 1.9 Map the static files

In the **Web** tab, find the **Static files** section and add **two** mappings,
one row each (URL → Directory):

| URL | Directory |
| --- | --- |
| `/static/` | `/home/YOURNAME/Jakeala_Naturals/backend/staticfiles` |
| `/media/` | `/home/YOURNAME/Jakeala_Naturals/backend/media` |

`/static/` is what makes the Django admin look right. Both folders exist because
you ran `collectstatic` in step 1.6 (create `media` if missing:
`mkdir -p ~/Jakeala_Naturals/backend/media`).

### 1.10 Reload and test

Click the big green **Reload** button, then check these URLs in your browser:

| URL | Expected |
| --- | --- |
| `https://YOURNAME.pythonanywhere.com/api/products/` | JSON list of products |
| `https://YOURNAME.pythonanywhere.com/api/categories/` | JSON list of categories |
| `https://YOURNAME.pythonanywhere.com/api/articles/` | JSON list of articles |
| `https://YOURNAME.pythonanywhere.com/admin/` | Django admin login page **with styling** |

If a page returns an error or `DisallowedHost`, open the **Error log** link on the
Web tab — it shows the exact Python traceback. Most first-deploy problems are a
typo in `ALLOWED_HOSTS` or a wrong `PROJECT_DIR` in the WSGI file.

**You now have a live API.** Note the base URL, `https://YOURNAME.pythonanywhere.com/api`
— both Vercel and the admin dashboard need it.


---

## Part 2 — Front end on Vercel

Vercel is the natural home for Next.js and the free tier is generous: static
pages, SSL and a global CDN out of the box.

### 2.1 Import the project

1. Sign in at <https://vercel.com> with your GitHub account.
2. **Add New… → Project → Import** `Ikolawole2020/Jakeala_Naturals`.
3. **Root Directory** → click *Edit* and choose **`frontend`**.
   This is the single most important setting: the repo root holds the Django
   backend too, and Vercel must not try to build that.
4. Framework Preset detects **Next.js** automatically. Leave the build command
   and output directory alone (Vercel uses its own, so the local `.next`
   cache-cleaning script does not interfere).

### 2.2 Set the environment variables

Expand **Environment Variables** and add these three (tick *Production*,
*Preview* and *Development*):

| Name | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://YOURNAME.pythonanywhere.com/api` |
| `NEXT_PUBLIC_SITE_URL` | `https://jakeala.com` (or your `.vercel.app` URL for now) |
| `NEXT_PUBLIC_SITE_EMAIL` | `info@jakeala.com` |

`NEXT_PUBLIC_*` values are baked in **at build time**, so if you change one you
must redeploy before it takes effect.

### 2.3 Deploy

Click **Deploy**. The build publishes roughly 19 routes.

The front end is written so a build **never fails because the API is down**: if a
request to Django fails, pages fall back to built-in catalogue data. So you can
deploy the site before the API is perfect, and it starts showing live data as
soon as the API answers.

### 2.4 Tell the backend to trust the front end

Copy the domain Vercel gave you (e.g. `https://jakeala-naturals.vercel.app`), then
in the PythonAnywhere console:

```bash
cd ~/Jakeala_Naturals/backend
nano .env
```

Update the CORS line to include the Vercel domain, then save:

```ini
CORS_ALLOWED_ORIGINS=https://jakeala.com,https://www.jakeala.com,https://jakeala-naturals.vercel.app
```

Reload the web app (Web tab → **Reload**), then open your Vercel URL — products
and articles should now come from the live API.

> If the site shows products but the **`/admin` dashboard** says *"Cannot connect
> to the backend"*, the cause is almost always `CORS_ALLOWED_ORIGINS`: the exact
> origin (scheme included, no trailing slash) must be listed. Check the browser
> console for a CORS error to confirm.


---

## Part 3 — Updating the live site

### 3.1 Normal workflow

```bash
# on your PC
git add -A
git commit -m "Describe the change"
git push
```

- **Vercel** redeploys the front end automatically. Nothing else to do.
- **PythonAnywhere** needs one command, in a Bash console:

```bash
cd ~/Jakeala_Naturals/backend && bash deploy.sh
```

Then press **Reload** on the Web tab.

### 3.2 Only front-end files changed?

Skip the backend entirely — Vercel has already handled it.

### 3.3 Only backend files changed?

```bash
cd ~/Jakeala_Naturals
git pull --ff-only
workon jakeala-venv
cd backend && python manage.py migrate && python manage.py collectstatic --noinput
```

Then **Reload**.

### 3.4 Change the admin password

The seeded password (`jakeala2026`) is public in this repository. Change it before
sharing the URL:

```bash
workon jakeala-venv
cd ~/Jakeala_Naturals/backend
python manage.py changepassword admin
```

### 3.5 Enable HTTPS-only

Once the site works over HTTPS, set this in `backend/.env` and reload:

```ini
DJANGO_SECURE_SSL_REDIRECT=1
```

PythonAnywhere terminates TLS at its proxy and `settings.py` already declares
`SECURE_PROXY_SSL_HEADER`, so Django detects HTTPS correctly and will not loop.

### 3.6 A custom domain

- **Front end** (jakeala.com): Vercel → Project → **Domains** → add `jakeala.com`
  and follow the DNS instructions. Then update `NEXT_PUBLIC_SITE_URL` and
  redeploy so canonicals, `sitemap.xml` and `robots.txt` use the new domain.
- **Backend**: custom domains on PythonAnywhere need a **paid plan**. On the free
  plan keep using `https://YOURNAME.pythonanywhere.com/api` — perfectly fine for
  an API. If you add one later, remember `ALLOWED_HOSTS` and
  `CSRF_TRUSTED_ORIGINS`.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `DisallowedHost` in the error log | Host missing from `ALLOWED_HOSTS` | Add the exact hostname (no scheme) and reload |
| API works but browser shows a **CORS** error | Front-end origin not allowed | Add the exact origin to `CORS_ALLOWED_ORIGINS` and reload |
| Django admin renders **unstyled** | `/static/` mapping missing or wrong path | Re-check the mapping points at `backend/staticfiles`, and re-run `collectstatic` |
| Admin login POST → **403 CSRF** | Origin missing from `CSRF_TRUSTED_ORIGINS` | Add `https://YOURNAME.pythonanywhere.com` and reload |
| Web app will not start at all | Placeholder `DJANGO_SECRET_KEY` with `DJANGO_DEBUG=0` | This is the built-in guard. Generate a real key (`python -c "import secrets; print(secrets.token_urlsafe(64))"`) and put it in `.env` |
| `ModuleNotFoundError: config` | WSGI `PROJECT_DIR` wrong | It must be the folder containing `manage.py` |
| `No module named dotenv` | requirements not installed in the virtualenv | `workon jakeala-venv && pip install -r requirements.txt` |
| Front end shows placeholder products | `NEXT_PUBLIC_API_URL` wrong or API unreachable | Fix the var and **redeploy** (it is baked in at build time) |
| Local pages look unstyled / routes 404 after editing | Stale `.next` cache from a running dev server | Stop the server, run `npm run dev` (it clears `.next` automatically), then hard-refresh with `Ctrl+F5` |

PythonAnywhere's own debugging guides are worth bookmarking:
- <https://help.pythonanywhere.com/pages/DebuggingImportError>
- <https://help.pythonanywhere.com/pages/DebuggingStaticFiles>

