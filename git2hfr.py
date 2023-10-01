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
                #raise EnvironmentError(f"Environment variable {var} is not set.")
                print(f"[ERROR] Environment variable {var} is not set.")
                sys.exit(1)

        return env_vars_dict

    def get(self, key):
        return self.env_vars.get(key)

class Hfr:
    BASE_URL = "https://forum.hardware.fr"

    def __init__(self):
        self.session = requests.Session()
        self.is_authenticated = False

    def _exit_with_error(self, message):
        print(f"[ERROR] {message}")
        sys.exit(1)

    def _get_hash_value(self):
        if self.is_authenticated == True:
            profile_response = self.session.get(f"{self.BASE_URL}/user/editprofil.php?config=hardwarefr.inc")
            soup = BeautifulSoup(profile_response.text, 'html.parser')
            hash_input = soup.find('input', {'name': 'hash_check'})
            if hash_input:
                self.hash_value = hash_input['value']
                print(f"[INFO] Variable hash_value has been set: {self.hash_value}")
            else:
                print("[ERROR] Could not extract hash value.")
                sys.exit(1)
        else:
            print("[ERROR] User is not authentificated")
            sys.exit(1)

    def _get_category_values(self):
        try:
            response = self.session.get(f"{self.BASE_URL}/search.php?config=hfr.inc&cat=&subcat=")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            category_values = [option['value'] for option in soup.select('select[name="cat"] option') if option['value']]
            return category_values

        except requests.RequestException as e:
            print(f"[ERROR] Failed to get category values: {str(e)}")
            return []

    def login(self, pseudo, password):
        form_data = { "pseudo": pseudo, "password": password }

        try:
            response = self.session.post(f"{self.BASE_URL}/login_validation.php?config=hfr.inc", data=form_data)
            response.raise_for_status()

            if "Votre mot de passe ou nom d'utilisateur n'est pas valide" in response.text:
                print("[ERROR] Invalid credentials.")
            elif "Vérification de votre identification..." in response.text or "Votre identification sur notre forum s'est déroulée avec succès." in response.text:
                if self.session.cookies.get('md_user') == pseudo:
                    print("[INFO] Connection successful!")
                    self.pseudo = pseudo
                    self.is_authenticated = True
                    self._get_hash_value()
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

    def _generate_post_data(self, cat, subject, content, post=None, numreponse=None, dest=None ):
        category_values = self._get_category_values()

        if cat not in category_values:
            raise ValueError(f"La catégorie '{cat}' n'est pas valide. Les catégories valides sont {category_values}")
        
        self.cat = cat

        return {
            "hash_check": self.hash_value,
            "cat": self.cat,
            "content_form": content,
            "post": post,
            "numreponse": numreponse,
            "dest": dest,
            "sujet": subject,
            "parents": "",
            "stickold": "",
            "new": "0",
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
            "MsgIcon": "1",
            "search_smilies": "",
            "ColorUsedMem": "",
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
    # Vérification préalable des entrées
    if not content:
        self._exit_with_error("Content is missing.")
    if not subject:
        self._exit_with_error("Subject is missing.")

    post_data = self._generate_post_data(
        cat="prive",
        subject=subject,
        content=content,
        dest=dest
    )
    response = self.session.post(f"{self.BASE_URL}/bddpost.php", data=post_data)

    error_messages = {
        "Vous devez entrez un destinataire pour envoyer un message privé": "Destinataire missing.",
        "Vous devez remplir tous les champs avant de poster ce message": "Content or subject missing.",
        "Afin de prevenir les tentatives de flood, vous ne pouvez poster plus de 1 nouveaux sujets consécutifs dans un intervalle de 60 minutes": "Limit reached."
    }

    for error in error_messages:
        if error in response.text:
            self._exit_with_error(f"Server: {error_messages[error]}")

    succeed_message = "Votre message a été posté avec succès !"
    if succeed_message in response.text:
        print(f"------\n{succeed_message}")
        sys.exit(0)
    else:
        self._exit_with_error(response.text)

def edit_post(self, cat, post, numreponse, content):
    # Vérification préalable des entrées
    if not cat:
        self._exit_with_error("Category number is missing.")
    if not content:
        self._exit_with_error("Content is missing.")
    if not post:
        self._exit_with_error("Topic number is missing.")
    if not numreponse:
        self._exit_with_error("Message number is missing.")

    post_data = self._generate_post_data(
        cat=cat,
        subject="caca",  # c'est un placeholder ?
        content=content,
        dest="",
        post=post,
        numreponse=numreponse
    )
    response = self.session.post(f"{self.BASE_URL}/bdd.php", data=post_data)

    error_messages = {
        "Vous n'avez pas les droits pour éditer ce message !": "Server: No rights to edit this message. Wrong message selected?",
        "Ce message ne vous est pas destiné, désolé": "Server: This message is not for you. Wrong topic number?"
    }

    for error in error_messages:
        if error in response.text:
            self._exit_with_error(error_messages[error])

    succeed_message = "Votre message a été édité avec succès !"
    if succeed_message in response.text:
        print(f"------\n{succeed_message}")
    else:
        self._exit_with_error(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send a message on HFR forum.')
    parser.add_argument('--cat', type=str, required=True, help='Forum categorie')
    parser.add_argument('--subject', type=str, required=False, help='Message subject')
    parser.add_argument('--content', type=str, required=False, help='Message content')
    parser.add_argument('--post', type=int, required=False, help='Topic number')
    parser.add_argument('--numreponse', type=int, required=False, help='Message number')
    parser.add_argument('--dest', type=str, required=False, help='Message destinataire')

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