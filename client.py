import requests
import re
import supersecret

s = requests.Session()

def login(s):
    # get initial session and nonce
    resp = s.get("https://dojo.pwn.college")
    nonce=re.findall(b"'csrfNonce': \"(.*)\"", resp.content)[0]

    login = supersecret.getSecret("dojo.pwn.college", "login")
    password = supersecret.getSecret("dojo.pwn.college", "password")
    resp = s.post("https://dojo.pwn.college", data = {
        "name": login,
        "password": password,
        "_submit": "Submit",
        "nonce": nonce
    })

