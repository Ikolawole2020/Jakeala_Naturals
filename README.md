# Jakeala Naturals

Production-ready natural wellness e-commerce platform.

**Stack:** Django 5 REST API + Next.js 14 (App Router)  
**Brand:** Warm, botanical, feminine, inclusive, modern and science-aware.

> **Going live?** See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for the full
> PythonAnywhere (backend) + Vercel (frontend) walkthrough, environment
> variables, and a troubleshooting table.

## Brand

- Primary green `#52805A`
- Soft green `#689F74`
- CTA orange `#E67E22`
- Gold `#F39C12`
- Slogan: *Where every skin is our priority*
- Hero: *Natural Wellness. Thoughtfully Made.*

## Quick start

**One command (Windows):** double-click `dev.bat` in the repo root. It opens two windows — Django on `:8000` (runs `migrate` + `seed` automatically) and Next.js on `:3000`.

**Manual:**

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver 8000
```

Admin: http://localhost:8000/admin  
API: http://localhost:8000/api/

Default admin (after seed): `admin` / `jakeala2026`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

`npm run dev` and `npm run build` now **auto-clear the `.next` cache** first (avoids stale-build styling/route glitches). `npm run clean` does it manually.
If port 3000 is held by an old process, stop it first (`Ctrl + C` in its terminal, then `netstat -ano | findstr :3000`).

Open http://localhost:3000

## Features

- Homepage: hero, category gateways, brand promise, featured products, education, trust, newsletter
- Category & collection pages
- Product detail pages with ingredients, directions, warnings, FAQs, related products, add to cart
- Cart drawer + checkout
- Customer accounts (register / login / orders)
- Wellness / blog
- About / brand story
- Contact & wholesale inquiry
- Newsletter capture
- Legal pages (privacy, terms, shipping, accessibility)
- SEO: metadata + canonical URLs, product JSON-LD, sitemap.xml + robots.txt, clean URLs
- 404 + error pages, mobile-first accessible UI, sticky mobile add-to-cart

## Routes

| Path | Page |
| --- | --- |
| `/` | Home (hero, categories, promise, featured, education, trust, newsletter) |
| `/shop` | Catalog (search via `?q=`) |
| `/category/[slug]` | Collection (womens-wellness, essential-oils, eye-health, skin-body) |
| `/product/[slug]` | Product detail (gallery, buy box, ingredients, directions, warnings, FAQs, reviews, related, sticky cart, JSON-LD) |
| `/wellness` / `/wellness/[slug]` | Wellness journal index + article |
| `/about` `/contact` `/wholesale` | Brand story, support, wholesale inquiry |
| `/account` | Sign in / register + order tracking by email |
| `/checkout` | Secure checkout |
| `/legal/privacy` `/legal/terms` `/legal/shipping` `/legal/accessibility` | Legal & trust policies |
| `/admin` | Custom staff dashboard (login at `/admin/login`) — products, categories, orders, reviews, articles, subscribers, messages |
| `/sitemap.xml` `/robots.txt` | SEO files |

## Admin

Two admin surfaces are available:

- **`/admin`** (in-app dashboard): sign in with a staff account at `/admin/login`. Once in, you can add/edit/delete **products** and **categories**, manage **orders** (view + update status), moderate **reviews**, publish **articles**, and view/delete **subscribers** and **contact messages**. Token-authenticated against the Django backend (`/api/admin/*`, staff-only).
- **Django admin** at `http://localhost:8000/admin`: the full-featured fallback for anything the dashboard doesn't expose.

Default staff login (after `python manage.py seed`): **`admin` / `jakeala2026`**

`seed` is self-healing: it always ensures the `admin` account exists, is
staff/superuser/active, and that the password above actually works (it repairs
the password if it can't be matched). Force the reset with:

```bash
python manage.py seed --reset-admin-password
```

New staff users: create them in the Django admin (Auth → Users, tick *staff* status).

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Admin login shows **"Cannot connect to the backend"** | Django isn't running, so `fetch` fails at the network layer (this is *not* a wrong password) | Start the backend: `cd backend && python manage.py runserver 8000`. Check `netstat -ano \| findstr :8000` shows a listener. |
| Admin login shows **"Invalid credentials or not a staff account."** | Wrong password, or the account isn't staff | `python manage.py seed --reset-admin-password` then use `admin` / `jakeala2026` |
| Catalogue/products load empty everywhere | Backend down | Same as row 1 |
| Pages unstyled, or `/admin` 404s, after edits | Stale `.next` cache / an old dev server still serving | Stop the running server (`Ctrl + C`), then `npm run dev` (it auto-clears `.next`). Hard-refresh with `Ctrl + F5`. |
| Port 3000 or 8000 already in use | An old process is still listening | `netstat -ano \| findstr :3000` → `taskkill /PID <pid> /F` |
| Port 3000 answers but the page is blank/unstyled and no dev server is running | Another program (e.g. a VPN service like `EonVPNRoutingService.exe`) is holding `127.0.0.1:3000`. It accepts connections but doesn't speak HTTP, so the browser hangs | Either start the dev server, or run the frontend on a free port: `npm run dev:3001` and open http://localhost:3001 |

The admin login page prints the exact API endpoint it calls, so you can always confirm what the frontend is talking to.


## Project layout

```
backend/          Django + DRF (catalog, commerce, content)
frontend/         Next.js 14 App Router (app/, components/, lib/api.js)
```
