import requests
import re
import os
from bs4 import BeautifulSoup

# Environment variables handling
env_vars_list = [
    "HFR_LOGIN",
    "HFR_PASSWD"
]
env_vars_unset = []
env_vars_dict = {}

for env_variable in env_vars_list:
    env_value = os.getenv(env_variable)
    if env_value is not None:
        env_vars_dict[env_variable] = env_value
    else:
        env_vars_unset.append(env_variable)

if len(env_vars_unset) == 0:
    for var_name in env_vars_list:
        globals()[var_name] = env_vars_dict.get(var_name)
    print("[INFO] All environment variables are set")
    
else:
    unset_vars = ', '.join(env_vars_unset)
    print(f"[ERROR] The following variable(s) are not set: {unset_vars}")
    exit(1)

class HFR:
    LOGIN_URL = "https://forum.hardware.fr/login_validation.php?config=hfr.inc"
    MP_URL = "https://forum.hardware.fr/message.php?config=hfr.inc&cat=prive&sond=&p=1&subcat=&dest={}&subcatgroup=0"
    BASE_MP_URL = "https://forum.hardware.fr/forum2.php?config=hfr.inc&cat=prive&post="
    RESPONSE_URL = "https://forum.hardware.fr/bddpost.php"

    def __init__(self):
        self.session = requests.Session()

    def login(self, pseudo, password):
        form_data = {
            "pseudo": pseudo,
            "password": password
        }

        try:
            response = self.session.post(self.LOGIN_URL, data=form_data)
            response.raise_for_status()

            if "Votre mot de passe ou nom d'utilisateur n'est pas valide" in response.text:
                print("Login failed: Invalid username or password.")
                return
            elif "Vérification de votre identification..." in response.text or "Votre identification sur notre forum s'est déroulée avec succès." in response.text:
                profile_response = self.session.get("https://forum.hardware.fr/user/editprofil.php?config=hardwarefr.inc")
                profile_response.raise_for_status()

                soup = BeautifulSoup(profile_response.text, 'html.parser')
                pseudo_label = soup.find('td', class_='profilCase2', string=lambda s: 'Pseudo' in s)
                if pseudo_label:
                    profile_pseudo = pseudo_label.find_next_sibling('td').text.strip()

                    if profile_pseudo == pseudo:
                        print("Connection successful!")
                        self.pseudo = pseudo
                        return
                    else:
                        print("Login seems successful, but username mismatch detected.")
                        return
                else:
                    print("Failed to retrieve username from profile page. Login status unknown.")
                    return

            else:
                print("Unexpected response received. Login status unknown.")
                return

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect: {str(e)}")

    #def _hash_page() :
        # TODO: Handler to obtain page/post hash and data

    #def send_notification() :
        # TODO : Handler for sending notifications
        # - Either to subject (new message)
        # - Either private (new private message or use of last known conversation)

    #def edit_post() :
        # TODO: Post editing manager
        # - Either one or more posts (first post(s))

    def send_new_MP(self, dest, subject, content):
        # Get hash from page
        response = self.session.get(self.MP_URL.format(dest))
        html = response.text
        hash = re.search(r"hash_check.*?value=\"([a-z0-9]*)\"", html).group(1)

        # Build post data
        post_data = {
            "hash_check": hash,
            "parents": "",
            "post": "",
            "stickold": "",
            "new": "0",
            "cat": "prive",
            "numreponse": "",
            "numrep": "",
            "page": "1",
            "verifrequet": "1100",
            "p": "1",
            "sondage": "0",
            "sond": "0",
            "cache": "",
            "owntopic": "0",
            "config": "hfr.inc",
            "pseudo": self.pseudo,
            "password": self.password,
            "dest": dest,
            "sujet": subject,
            "MsgIcon": "1",
            "search_smilies": "",
            "ColorUsedMem": "",
            "content_form": content,
            "wysiwyg": "0",
            "submit": "Valider+votre+message",
            "signature": "1"
        }

        # Send MP
        response = self.session.post(self.RESPONSE_URL, data=post_data)
        print(response.status_code)

if __name__ == "__main__":
    h = HFR()
    h.login(HFR_LOGIN, HFR_PASSWD)
    h.send_new_MP("Ximothov", "Test script", "ça marche gros")
    # TODO: Add options
