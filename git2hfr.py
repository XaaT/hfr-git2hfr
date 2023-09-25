import requests
import re
import os
from bs4 import BeautifulSoup

class Config:
    def __init__(self):
        self.env_vars_list = [
            "HFR_LOGIN",
            "HFR_PASSWD"
        ]
        self.env_vars = self._get_env_vars()

    def _get_env_vars(self):
        env_vars_dict = {}

        for var in self.env_vars_list:
            value = os.getenv(var)
            if value:
                env_vars_dict[var] = value
            else:
                raise EnvironmentError(f"Environment variable {var} is not set.")

        return env_vars_dict

    def get(self, key):
        return self.env_vars.get(key)

class Hfr:
    LOGIN_URL = "https://forum.hardware.fr/login_validation.php?config=hfr.inc"
    MP_URL = "https://forum.hardware.fr/message.php?config=hfr.inc&cat=prive&sond=&p=1&subcat=&dest={}&subcatgroup=0"
    BASE_MP_URL = "https://forum.hardware.fr/forum2.php?config=hfr.inc&cat=prive&post="
    RESPONSE_URL = "https://forum.hardware.fr/bddpost.php"

    def __init__(self):
        self.session = requests.Session()
        self.is_authenticated = False

    def login(self, pseudo, password):
        form_data = {
            "pseudo": pseudo,
            "password": password
        }

        try:
            response = self.session.post(self.LOGIN_URL, data=form_data)
            response.raise_for_status()

            if "Votre mot de passe ou nom d'utilisateur n'est pas valide" in response.text:
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
                        self.is_authenticated = True
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
            "password": "",
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
    try:
        config = Config()
        h = Hfr()
        h.login(config.get("HFR_LOGIN"), config.get("HFR_PASSWD"))

        if not h.is_authenticated:  # vérification de l'authentification
            print("Authentication failed. Exiting script.")
            exit(1)

        h.send_new_MP("Ximothov", "Test script", "ça marche gros")
    except EnvironmentError as e:
        print(e)
        exit(1)
