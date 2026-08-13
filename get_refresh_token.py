"""
Run this ONCE on your own computer to authorize the school website to send
email through your tetelisarasankardev@gmail.com account via the Gmail API.

WHAT THIS DOES
--------------
It opens your browser, asks you to log into Gmail and approve
"send email as you", then prints a long-lived refresh token. You paste
that (plus your client ID and secret) into Render's environment variables,
and the website can then send email indefinitely without running this
script again.

SETUP BEFORE RUNNING
---------------------
1. pip install google-auth-oauthlib requests --break-system-packages
2. Download your OAuth client JSON from Google Cloud Console
   (APIs & Services -> Credentials -> your Desktop app client -> Download JSON)
3. Save it in this same folder as "client_secret.json"
4. Run:  python get_refresh_token.py
5. A browser tab opens -> log in as tetelisarasankardev@gmail.com -> allow.
   (You'll see an "unverified app" warning -- click "Advanced" ->
   "Go to School Site Mailer (unsafe)". This is expected and fine: it's
   your own app, just not submitted for Google's public-app review, which
   isn't needed since only you will ever use it.)
6. The script prints three values. Copy them into Render's Environment tab.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
credentials = flow.run_local_server(port=0)

print("\n" + "=" * 60)
print("Copy these three values into Render -> Environment tab:")
print("=" * 60)
print(f"GMAIL_CLIENT_ID     = {credentials.client_id}")
print(f"GMAIL_CLIENT_SECRET = {credentials.client_secret}")
print(f"GMAIL_REFRESH_TOKEN = {credentials.refresh_token}")
print("=" * 60)
