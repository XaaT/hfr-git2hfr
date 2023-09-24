import requests
import re
import os

# Environment variables handling
env_vars_list = ["HFR_LOGIN", "HFR_PASSWD"]
env_vars_unset = []
env_vars_dict = {}

for env_variable in env_vars_list:
    env_value = os.getenv(env_variable)
    if env_value is not None:
        env_vars_dict[env_value] = env_value
    else:
        env_vars_unset.append(env_variable)

if len(env_vars_unset) == 0:
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

    def connect(self, pseudo, password):
        self.pseudo = pseudo
        self.password = password
        form_data = {"pseudo": pseudo, "password": password}
        self.session.post(self.LOGIN_URL, data=form_data)

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
    h.connect(HFR_LOGIN, HFR_PASSWD)
    h.send_new_MP("Ximothov", "Test script", "ça marche gros")
