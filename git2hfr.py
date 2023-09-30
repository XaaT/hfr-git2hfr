import requests
import re
import os
from bs4 import BeautifulSoup
import argparse
import sys

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
    BASE_URL = "https://forum.hardware.fr"

    def __init__(self):
        self.session = requests.Session()
        self.is_authenticated = False

    def login(self, pseudo, password):
        form_data = { "pseudo": pseudo, "password": password }

        try:
            response = self.session.post(f"{self.BASE_URL}/login_validation.php?config=hfr.inc", data=form_data)
            response.raise_for_status()

            if "Votre mot de passe ou nom d'utilisateur n'est pas valide" in response.text:
                print("[ERROR] Invalid credentials.")
            elif "Vérification de votre identification..." in response.text or "Votre identification sur notre forum s'est déroulée avec succès." in response.text:
                profile_response = self.session.get(f"{self.BASE_URL}/user/editprofil.php?config=hardwarefr.inc")
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

    def _get_hash_from_page(self, url):
        response = self.session.get(url)
        response.raise_for_status()  # Ensure a successful response
        html = response.text
        match = re.search(r"hash_check.*?value=\"([a-z0-9]*)\"", html)
        if not match:
            raise ValueError("Hash value not found in the provided page.")
        return match.group(1)

    def _build_post_data(self, dest, subject, content, hash_value):
        return {
            "hash_check": hash_value,
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

    #def send_notification() :
        # TODO : Handler for sending notifications
        # - Either to subject (new message)
        # - Either private (new private message or use of last known conversation)

    #def edit_post() :
        # TODO: Post editing manager
        # - Either one or more posts (first post(s))

    def send_new_MP(self, dest, subject, content):
        hash_value = self._get_hash_from_page(f"{self.BASE_URL}/message.php?config=hfr.inc&cat=prive&sond=&p=1&subcat=&dest={dest}&subcatgroup=0".format(dest))
        post_data = self._build_post_data(dest, subject, content, hash_value)
        
        response = self.session.post(f"{self.BASE_URL}/bddpost.php", data=post_data)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Received status code: {response.status_code}")

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
            sys.exit(1)

        hfr.send_new_MP(args.user, args.subject, args.content)
    except EnvironmentError as e:
        print(e)
        sys.exit(1)