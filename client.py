import requests
import re
import supersecret
import argparse
import bs4

ENDPOINT="dojo.pwn.college"

s = requests.Session()

def login(s):
    # get initial session and nonce
    resp = s.get(f"https://{ENDPOINT}")
    nonce=re.findall(b"'csrfNonce': \"(.*)\"", resp.content)[0]

    login = supersecret.getSecret(f"{ENDPOINT}", "login")
    password = supersecret.getSecret(f"{ENDPOINT}", "password")
    resp = s.post(f"https://{ENDPOINT}/login", data = {
        "name": login,
        "password": password,
        "_submit": "Submit",
        "nonce": nonce
    })
    return resp

def categories(s):
    resp = s.get(f"https://{ENDPOINT}/challenges")
    soup = bs4.BeautifulSoup(resp.content, "lxml")
    cards = soup.find_all("div", {"class": "card-body"})
    cards = [(card.h4.text.strip(), card.p.text.strip().split(" / "), card.parent.parent["href"]) for card in cards]
    return cards 

def challenges(s, category):
    resp = s.get(f"https://{ENDPOINT}/challenges/{category}")
    nonce=re.findall(b"'csrfNonce': \"(.*)\"", resp.content)[0]
    soup = bs4.BeautifulSoup(resp.content, "lxml")
    cards = soup.find_all("div", {"id": "challenges"})[0].find_all("div", {"class": "card"})
    cards = [(card.h4.text.strip(), int(card.find_all("input", {"id": "challenge-id"})[0]["value"])) for card in cards]
    return (cards, nonce)

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")
    subparser.add_parser("login")
    subparser.add_parser("categories")
    challenges_parser = subparser.add_parser("challenges")
    challenges_parser.add_argument("category")
    start_parser = subparser.add_parser("start")
    start_parser.add_argument("category")
    start_parser.add_argument("problem")
    options = parser.parse_args()

    if supersecret.hasSecret(f"{ENDPOINT}", "session"):
        s.cookies["session"] = supersecret.getSecret(f"{ENDPOINT}", "session")

    if options.command == "login":
        result = login(s)
        if result.ok:
            supersecret.storeSecret(f"{ENDPOINT}", "session", s.cookies["session"])
        else:
            print("Failed to login!", result.status_code, result.reason)
    elif options.command == "categories":
        for category in categories(s):
            name, (solved, total), href = category
            print(f"{name} {solved} / {total} [{href}]")
    elif options.command == "challenges":
        for challenge in challenges(s, options.category):
            print(challenge)
    elif options.command == "start":
        chals, nonce = challenges(s, options.category)
        for chal in chals:
            if chal[0] == options.problem:
                name, chal_id = chal
                resp = s.post(f"https://{ENDPOINT}/pwncollege_api/v1/docker", json = {
                        "challenge_id": chal_id,
                        "practice": False
                    },
                    headers={
                        "CSRF-Token": str(nonce, "UTF-8")
                    })
                break
        else:
            print(f"Could not find challnege {options.challenge} for {options.category}")
    else:
        print(options)
        print("No command specified!")

if __name__=="__main__":
    main()
