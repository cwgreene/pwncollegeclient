import requests
import re
import supersecret
import subprocess
import argparse
import bs4

ENDPOINT="dojo.pwn.college"

s = requests.Session()

challenges_dict = {}

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
    if category in challenges_dict:
        return challenges_dict[category]
    resp = s.get(f"https://{ENDPOINT}/challenges/{category}")
    nonce= re.findall(b"'csrfNonce': \"(.*)\"", resp.content)[0]
    soup = bs4.BeautifulSoup(resp.content, "lxml")
    cards = soup.find_all("div", {"id": "challenges"})[0].find_all("div", {"class": "card"})
    cards = [(card.h4.text.strip(), int(card.find_all("input", {"id": "challenge-id"})[0]["value"])) for card in cards]
    challenges_dict[category] = (cards, nonce)
    return (cards, nonce)

def activate_challenge(s, category, problem, practice=False):
    chals, nonce = challenges(s, category)
    for chal in chals:
        if problem in chal[0]:
            name, chal_id = chal
            resp = s.post(f"https://{ENDPOINT}/pwncollege_api/v1/docker", json = {
                    "challenge_id": chal_id,
                    "practice": practice
                },
                headers={
                    "CSRF-Token": str(nonce, "UTF-8")
                })
            break
    else:
        print(f"Could not find challnege {problem} for {category}")
        print("Problems found:")
        for chal in chals:
            print(" ", chal[0])
        

def download_challenge(s, category, challenge_id, target_dir, pratice):
    activate_challenge(s, category, challenge_id, practice)
    p = subprocess.Popen(["scp", "hacker@dojo.pwn.college:/challenge/*", target_dir])
    p.wait()

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
    start_parser.add_argument("--practice", action="store_true", default=False)
    start_parser = subparser.add_parser("download")
    start_parser.add_argument("category")
    start_parser.add_argument("problem")
    start_parser.add_argument("target_dir")
    start_parser = subparser.add_parser("download-all")
    start_parser.add_argument("category")
    start_parser.add_argument("target_dir")
    options = parser.parse_args()

    if supersecret.hasSecret(f"{ENDPOINT}", "session"):
        s.cookies["session"] = supersecret.getSecret(f"{ENDPOINT}", "session")

    if options.command == "login":
        s.cookies.clear()
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
        chals, nonce = challenges(s, options.category)
        for challenge in chals:
            print(challenge)
    elif options.command == "start":
        activate_challenge(s, options.category, options.problem, options.practice)
    elif options.command == "download":
        download_challenge(s, options.category, options.problem, options.target_dir)
    elif options.command == "download-all":
        chals, nonce = challenges(s, options.category)
        for (problem, id) in chals:
            download_challenge(s, options.category, problem, options.target_dir)
    else:
        print(options)
        print("No command specified!")

if __name__=="__main__":
    main()
