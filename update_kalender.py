import requests
import urllib3
import base64
import json
import os
import re

# Configuratie

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME")
ICS_FILENAME = "volleykalender.ics"


# SSL-verificatie uitschakelen voor bedrijfsnetwerken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ICS-bronnen van VolleyScores
urls = [
    "https://www.volleyscores.be/calendar/team/92669",
    "https://www.volleyscores.be/calendar/team/92662",
    "https://www.volleyscores.be/calendar/team/92670",
    "https://www.volleyscores.be/calendar/team/92665",
    "https://www.volleyscores.be/calendar/team/93447"
]


team_name_replacements = {
    "Forza EVO Volley OUDENAARDE": "FEVO",
    "Forza EVO Volley OUDENAARDE U15 B meisjes": "FEVO U15B M",
    "Forza EVO Volley OUDENAARDE U13 A meisjes": "FEVO U13A M",
    "Forza EVO Volley OUDENAARDE U17 jongens": "FEVO U17 J",
    "Forza EVO Volley OUDENAARDE U11 A meisjes": "FEVO U11A M",
    "Forza EVO Volley OUDENAARDE U17 meisjes": "FEVO U17 M",
    "Volley Team Zwijnaarde B": "VT Zwijnaarde B",
    "VC Zandhoven U15 A meisjes": "Zandhoven U15A M"
    # voeg meer als nodig
}


# ICS combineren
combined_ics = ""
for url in urls:
    response = requests.get(url, verify=False)
    content = response.text
    body = content.replace("BEGIN:VCALENDAR", "").replace("END:VCALENDAR", "").strip()
    combined_ics += body + "\n"

for long_name, short_name in team_name_replacements.items():
    final_ics = final_ics.replace(long_name, short_name)
    
 
# Verwijder code vóór dubbelepunt in SUMMARY
final_ics = re.sub(r'^SUMMARY:[^:]+: ?', 'SUMMARY: ', final_ics, flags=re.MULTILINE)


final_ics = "BEGIN:VCALENDAR\nVERSION:2.0\n" + combined_ics + "END:VCALENDAR"

# GitHub API upload
api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{ICS_FILENAME}"

# Bestaat het bestand al? -> SHA ophalen
response = requests.get(api_url, headers={
    "Authorization": f"token {GITHUB_TOKEN}"
})
if response.status_code == 200:
    sha = response.json()["sha"]
else:
    sha = None

# Upload nieuwe versie
payload = {
    "message": "Automatische upload van gecombineerde volleykalender",
    "content": base64.b64encode(final_ics.encode()).decode(),
    "branch": "main"
}
if sha:
    payload["sha"] = sha

upload_response = requests.put(api_url, headers={
    "Authorization": f"token {GITHUB_TOKEN}"
}, data=json.dumps(payload))

if upload_response.status_code in [200, 201]:
    print("✅ Upload geslaagd!")
    public_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{ICS_FILENAME}"
    print("📅 Je kalender is beschikbaar op:")
    print(public_url)
else:
    print("❌ Upload mislukt:")
    print(upload_response.status_code)
    print(upload_response.text)
