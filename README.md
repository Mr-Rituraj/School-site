# Sankardev Sishu Niketan, Tetelisara — Website

A full-stack school website: Flask backend + Jinja templates + vanilla CSS/JS frontend,
branded with the school's own crest.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

The first run creates `school.db` (SQLite) and seeds a few sample notices automatically.

## What's included

- **Home** — hero banner with the school crest, quick links, an achievements slideshow,
  a photo slideshow, and latest notices
- **Academics** — six departments with their subjects
- **Admissions** — the actual 4-step application process
- **Faculty** — staff directory
- **Notices** — full noticeboard, backed by SQLite
- **Contact** — form that saves messages to the database (`messages` table) and emails
  a notification to the front office
- **Admin** (`/admin/login`, linked from the footer as "Staff login") — password-protected
  page to view every submitted message in a table

## Email notifications

Every contact-form submission emails **tetelisarasankardev@gmail.com**, sent through
**Google's own Gmail API** rather than a third-party relay. This is important: Render's
free tier blocks raw SMTP entirely, and third-party relays (like Brevo) sending mail with
a `@gmail.com` "From" address get deferred/spam-filtered by Gmail's own strict
authentication rules. Sending through the Gmail API sidesteps both problems — it's an
HTTPS call (not blocked), and it's genuinely Google sending on your behalf (not spoofing).

**One-time setup (free, ~10 minutes):**

1. Go to https://console.cloud.google.com, log in as `tetelisarasankardev@gmail.com`,
   and create a new project.
2. **APIs & Services → Library** → search **Gmail API** → **Enable**.
3. **APIs & Services → OAuth consent screen** → User type **External** → fill in the
   required fields → add `tetelisarasankardev@gmail.com` as a test user → Save.
4. **APIs & Services → Credentials** → **+ Create Credentials → OAuth client ID** →
   Application type **Desktop app** → Create → **Download JSON**.
5. Save that downloaded file as `client_secret.json` in this project folder.
6. On your own computer, install the one-time helper library and run the included script:
   ```bash
   pip install google-auth-oauthlib --break-system-packages
   python get_refresh_token.py
   ```
7. A browser tab opens — log in as `tetelisarasankardev@gmail.com` and click **Allow**.
   You'll see an "unverified app" warning first — click **Advanced →
   Go to School Site Mailer (unsafe)**. This is expected: it's your own private app, not
   submitted for Google's public review, which isn't necessary since only this account
   uses it.
8. The script prints three values: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`,
   `GMAIL_REFRESH_TOKEN`. Set all three as environment variables wherever the app runs.

**Locally:**
```bash
export GMAIL_CLIENT_ID="..."
export GMAIL_CLIENT_SECRET="..."
export GMAIL_REFRESH_TOKEN="..."
python app.py
```

**On Render:** Dashboard → your service → **Environment** tab → add all three → Save
(triggers a redeploy).

If these aren't set, the contact form still works and still saves to the database — it
just skips sending the email and logs a note to the console instead of failing.

**Note:** `client_secret.json` and `get_refresh_token.py` are only needed for this
one-time setup on your own computer — never commit `client_secret.json` to GitHub (it's
already in `.gitignore`). The running website only ever needs the three environment
variables above, not the JSON file itself.

## Admin password

Set `ADMIN_PASSWORD` the same way (locally via `export`, on Render via the Environment
tab) — otherwise it falls back to the default `changeme123`, which anyone could guess.

## About the images

- `static/img/logo.png` is the real school crest — used in the header, footer, browser
  favicon, and as a watermark on the hero banner.
- `static/img/gallery/*.svg` are original flat-vector illustrations (classroom, sports day,
  Bihu/cultural day, science lab, annual day) standing in for real school photos, since I
  don't have access to your actual photographs. **Swap these out**: drop real photos into
  `static/img/gallery/` (e.g. `annualday.jpg`) and update the `GALLERY` list near the top
  of `app.py` to point at the new filenames — the slideshow will pick them up automatically.

## Structure

```
app.py                 Flask app, routes, SQLite setup
templates/              Jinja2 HTML templates (base.html + one per page)
static/css/style.css    All styling, design tokens at the top
static/js/script.js     Live bell-schedule ticker, scroll reveals, mobile menu
requirements.txt
```

## Customizing

- Edit `DEPARTMENTS`, `FACULTY`, `ADMISSIONS_STEPS`, `BELL_SCHEDULE`, `ACHIEVEMENTS`, and
  `GALLERY` in `app.py` for your own school's data.
- Notices are stored in SQLite — insert new ones with a small script or hook up an admin form later.
- Colors, fonts and spacing are all defined as CSS custom properties at the top of
  `style.css` under `:root` (tuned to the crest's navy/gold palette).
