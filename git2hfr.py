import requests
import re
class HFR:
    LOGIN_URL = "https://forum.hardware.fr/login_validation.php?config=hfr.inc"
    MP_URL = "https://forum.hardware.fr/message.php?config=hfr.inc&cat=prive&sond=&p=1&subcat=&dest={}&subcatgroup=0"
    BASE_MP_URL = "https://forum.hardware.fr/forum2.php?config=hfr.inc&cat=prive&post="
    RESPONSE_URL = "https://forum.hardware.fr/bddpost.php"
    def __init__(self):
        self.session = requests.Session()
    def connect(self, pseudo, password):
        self.pseudo = pseudo,
        self.password = password
        form_data = {'pseudo': pseudo, 'password': password}
        self.session.post(HFR.LOGIN_URL, data=form_data)
    def send_new_MP(self, dest, sujet, content):
        # get hash from page
        response = self.session.get(HFR.MP_URL.format(dest))
        html = response.text
        r = re.search("hash_check.*?value=\"([a-z0-9]*)\"", html)
        h = r.group(1)
        print("Hash: {}".format(h))
        post_data = {
            "hash_check": h,
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
            "sujet": sujet,
            "MsgIcon": "1",
            "search_smilies": "",
            "ColorUsedMem": "",
            "content_form": content,
            "wysiwyg": "0",
            "submit": "Valider+votre+message",
            "signature": "1"
        }
        response = self.session.post(HFR.RESPONSE_URL, data=post_data)
        print(response.status_code)
if __name__ == "__main__":
    h = HFR()
    h.connect("XaTriX", "1234" )
    h.send_new_MP("garath_", "Test script", "ça marche gros" )
