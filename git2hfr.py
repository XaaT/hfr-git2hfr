import requests
import re
import os
from bs4 import BeautifulSoup
import argparse

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
        form_data = { "pseudo": pseudo, "password": password }

        try:
            response = self.session.post(self.LOGIN_URL, data=form_data)
            response.raise_for_status()

            if "Votre mot de passe ou nom d'utilisateur n'est pas valide" in response.text:
                print("[ERROR] Invalid credentials.")
            elif "Vérification de votre identification..." in response.text or "Votre identification sur notre forum s'est déroulée avec succès." in response.text:
                profile_response = self.session.get("https://forum.hardware.fr/user/editprofil.php?config=hardwarefr.inc")
                profile_response.raise_for_status()

                soup = BeautifulSoup(profile_response.text, 'html.parser')
                pseudo_label = soup.find('td', class_='profilCase2', string=lambda s: 'Pseudo' in s)

                if pseudo_label and pseudo_label.find_next_sibling('td').text.strip() == pseudo:
                    print("[INFO] Connection successful!")
                    self.pseudo = pseudo
                    self.is_authenticated = True
                else:
                    print("[WARNING] Login issues detected.")
            else:
                print("[WARNING] Unexpected response received. Login status unknown.")

        except requests.RequestException as e:
            raise ConnectionError(f"[ERROR] Failed to connect: {str(e)}")

    def get_github_file_content(self, repo_url):
        if 'github.com' in repo_url and 'raw' not in repo_url:
            repo_url = repo_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')

        response = requests.get(repo_url)
        response.raise_for_status()
        return response.text

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
    parser = argparse.ArgumentParser(description='Send a message on HFR forum.')
    parser.add_argument('--user', type=str, required=True, help='Recipient username')
    parser.add_argument('--subject', type=str, required=True, help='Message subject')
    parser.add_argument('--content', type=str, required=True, help='Message content')

    args = parser.parse_args()

    try:
        config = Config()
        hfr = Hfr()
        hfr.login(config.get("HFR_LOGIN"), config.get("HFR_PASSWD"))

        if not hfr.is_authenticated:
            print("[ERROR] Authentication failed. Exiting script.")
            exit(1)

        hfr.send_new_MP(args.user, args.subject, args.content)
    except EnvironmentError as e:
        print(e)
        exit(1)