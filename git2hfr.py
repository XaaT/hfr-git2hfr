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

    def __init__(self, debug=False):
        self.session = requests.Session()
        self.is_authenticated = False
        self.debug = debug

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
            else:
                self._exit_with_error("Could not extract hash value.")
        else:
            self._exit_with_error("User is not authenticated.")

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
                raise ValueError("Invalid credentials.")
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
            raise ConnectionError(f"Failed to connect: {str(e)}")

    def get_github_file_content(self, repo_url):
        if 'github.com' in repo_url and 'raw' not in repo_url:
            repo_url = repo_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')

        response = requests.get(repo_url)
        response.raise_for_status()
        return response.text

    def identify_page_and_extract_subcat(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")

        # Check if "sujet" input is hidden
        sujet_input = soup.find("input", {"name": "sujet"})
        is_hidden = "hidden" in sujet_input.get("type", "") if sujet_input else False

        # Check if the page is FP and extract "subcat" if it is
        if not is_hidden:
            subcat_input = soup.find('option', selected=True)
            subcat_value = subcat_input['value'] if subcat_input else None
            subject_name = sujet_input['value']
            return True, subcat_value, subject_name
        else:
            return False, None, None

    def _generate_post_data(self, cat, subject, content, post=None, numreponse=None, dest=None, subcat=None ):
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
            "subcat": subcat,
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
        if self.debug:
            print(f"Sending the following data for edit post: {post_data}")
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
        else:
            self._exit_with_error(response.text)

    def check_parameters(self, params):
        for param_name, param_value in params.items():
            if not param_value:
                self._exit_with_error(f"{param_name} is missing.")

    def edit_post(self, cat, post, numreponse, content):
        # Check if the necessary parameters are provided
        params = {"Category number": cat, "Content": content, "Topic number": post, "Message number": numreponse}
        self.check_parameters(params)

        # Build the URL for the editing page
        edit_url = f"{self.BASE_URL}/message.php?config=hfr.inc&cat={cat}&post={post}&numreponse={numreponse}"

        # Retrieve and parse the HTML of the editing page
        edit_page_html = self.session.get(edit_url).text

        # Identify the page type and extract "subcat" if it's a FP
        is_fp, subcat, subject = self.identify_page_and_extract_subcat(edit_page_html)

        # Edit the post
        if is_fp:
            post_data = self._generate_post_data(
                cat=cat,
                subject=subject,
                content=content,
                subcat=subcat,
                dest="",
                post=post,
                numreponse=numreponse
            )
            response = self.session.post(f"{self.BASE_URL}/bdd.php", data=post_data)
        else:
            post_data = self._generate_post_data(
                cat=cat,
                subject=self.pseudo,  # Obligatoire de foutre un truc random sinon ça couine, saloperie de forum
                content=content,
                dest="",
                post=post,
                numreponse=numreponse
            )
            response = self.session.post(f"{self.BASE_URL}/bdd.php", data=post_data)

        if self.debug:
            print(f"Sending the following data for edit post: {post_data}")

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

    def get_content(self, content_arg, file_arg, string_arg, github_arg):
        if file_arg:
            with open(file_arg, "r") as f:
                return f.read()
        elif string_arg:
            return string_arg
        elif github_arg:
            return self.get_github_file_content(github_arg)
        else:
            return content_arg

def cli():
    import argparse

    parser = argparse.ArgumentParser(description="CLI interface for interacting with Hardware.fr forum.")

    # Authentication
    parser.add_argument("--login", nargs=2, metavar=("PSEUDO", "PASSWORD"), help="Login to the forum with pseudo and password.")
    parser.add_argument("--auto-login", action="store_true", help="Automatically login using HFR_LOGIN and HFR_PASSWD environment variables.")

    # Interaction with the forum
    parser.add_argument("--send-mp", nargs=2, metavar=("DEST", "SUBJECT"), help="Send a private message.")
    parser.add_argument("--post", nargs=2, metavar=("CAT", "SUBJECT"), help="Post a new topic in the specified category.")
    parser.add_argument("--edit-post", nargs=3, metavar=("CAT", "POST_NUM", "RESPONSE_NUM"), help="Edit an existing post.")

    # Content source
    parser.add_argument("--content-file", metavar="FILE_PATH", help="Specify a local file as content source.")
    parser.add_argument("--content-string", metavar="STRING", help="Specify a string as content source.")
    parser.add_argument("--content-github", metavar="REPO_URL", help="Fetch content from a file in a GitHub repository.")

    # Debug
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to display detailed information.")

    args = parser.parse_args()

    hfr = Hfr(debug=args.debug)

    # Check if no arguments are provided and display help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Check for auto-login argument and perform login if provided
    if args.auto_login:
        pseudo = os.environ.get("HFR_LOGIN")
        password = os.environ.get("HFR_PASSWD")
        if not pseudo or not password:
            print("Error: HFR_LOGIN and HFR_PASSWD environment variables must be set for auto-login.")
            sys.exit(1)
        hfr.login(pseudo, password)

    # Check for login argument and perform login if provided
    elif args.login:
        pseudo, password = args.login
        hfr.login(pseudo, password)

    # Determine content
    content = hfr.get_content(
        content_arg=None,
        file_arg=args.content_file,
        string_arg=args.content_string,
        github_arg=args.content_github
    )

    if not content:
      print("Error: No valid content provided. Please use --content-file, --content-string, or --content-github to specify the content.")
      sys.exit(1)

    # Check for send-mp argument and send a private message if provided
    if args.send_mp:
        dest, subject = args.send_mp
        hfr.send_new_MP(dest, subject, content)

    # Check for post argument and post a new topic if provided
    elif args.post:
        cat, subject = args.post
        # TODO: Implement the logic to post a new topic

    # Check for edit-post argument and edit a post if provided
    elif args.edit_post:
        cat, post_num, response_num = args.edit_post
        hfr.edit_post(cat, post_num, response_num, content)

if __name__ == "__main__":
    cli()
