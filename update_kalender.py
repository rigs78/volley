import requests
import urllib3
import os
import re
import base64  
import json

# Configuratie
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME")
ICS_FILENAME = "volleykalender.ics"

# SSL-verificatie uitschakelen voor bedrijfsnetwerken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ICS-bronnen van VolleyScores
urls = [
    "https://www.volleyscores.be/calendar/team/92669", #u17a beker Renee
    "https://www.volleyscores.be/calendar/team/92662", #u15 beker Anna
    "https://www.volleyscores.be/calendar/team/92670", #u17 beker Renee
    "https://www.volleyscores.be/calendar/team/92665", #u15 beker Anna
    "https://www.volleyscores.be/calendar/team/92654", #u15  Juul
    "https://www.volleyscores.be/calendar/team/92655", #u15 beker Juul
    "https://www.volleyscores.be/calendar/team/92657", #forza promo 3 Briek
    "https://www.volleyscores.be/calendar/team/92656", #forza u19  Briek
    "https://www.volleyscores.be/calendar/team/92658",  # beker promo F Briek 
    "https://www.volleyscores.be/calendar/team/92352", #gent promo 3 F Victor
    "https://www.volleyscores.be/calendar/team/92410", #beker u17 Victor
    "https://www.volleyscores.be/calendar/team/92405", # beker promo F Victor
    "https://rbfa-svc.bijnens.eu/api/GetTeamCalendar?code=rfbaKalender001&teamId=349355", # voetbal Ramon
    "https://www.volleyscores.be/calendar/team/93447" #michelbeke Ruben
]

# ICS combineren
combined_ics = ""
for url in urls:
    response = requests.get(url, verify=False)
    content = response.text
    body = content.replace("BEGIN:VCALENDAR", "").replace("END:VCALENDAR", "").strip()
    combined_ics += body + "\n"

final_ics = "BEGIN:VCALENDAR\nVERSION:2.0\n" + combined_ics + "END:VCALENDAR"

# ---------------------------
# Functie: ICS inhoud bewerken
# ---------------------------
def verwerk_ics(ics_inhoud):
    # Mapping van wedstrijdcodeprefix naar afkorting
    code_mappings = {
        "OMU17N2R1c": "M17A",
        "OMU17N2R1e": "M17B",
        "OMU15N1R1c": "M15A",
        "OBM17": "Beker M17",
        "OBM15": "Beker M15",
        "OBJ15": "Beker J15",
        "OBJ19": "Beker J19",
        "OHP3B": "HP3",
        "U15": "JAGO",
        "OJU17/19N1R1": "J19",
        "OJU15N2R1c": "J15",
        "LIGD": "LIGD"
    }

    def vervang_summary(match):
        fullcode = match.group(1)  # bv. OMU17N2R1c-0014
        rest = match.group(2)      # bv. VC Hebo BORSBEKE-HERZELE B - FEVO A
        prefix = fullcode.split("-")[0]  # enkel OMU17N2R1c
        mapped = code_mappings.get(prefix)
        if mapped:
            return f"SUMMARY:{mapped}: {rest}"
        else:
            return f"SUMMARY: {rest}"

    # Corrigeer alle SUMMARY-regels
    ics_inhoud = re.sub(
        r'^SUMMARY:([A-Za-z0-9\-]+): ?(.*)$',
        vervang_summary,
        ics_inhoud,
        flags=re.MULTILINE
    )

    # Teamnaamverkortingen
    team_name_replacements = {
        "Forza Evo Volley OUDENAARDE": "FEVO",
        "Vlavo Saturnus Michelbeke A": "Michelbeke"
    }

    for lang, kort in team_name_replacements.items():
        ics_inhoud = ics_inhoud.replace(lang, kort)

    return ics_inhoud


# ICS-inhoud bewerken
final_ics = verwerk_ics(final_ics)


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


# Opslaan als ICS-bestand
#with open("gecombineerde_volley_kalender.ics", "w", encoding="utf-8") as file:
#    file.write(final_ics)

#print("✅ Gecombineerde kalender opgeslagen als 'gecombineerde_volley_kalender.ics'")




