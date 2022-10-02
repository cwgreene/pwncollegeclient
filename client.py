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

def dojos(s, options):
    resp = s.get(f"https://{ENDPOINT}/dojos")
    soup = bs4.BeautifulSoup(resp.content, "lxml")
    cards = soup.find_all("div", {"class": "card-body"})
    cards = [(card.h4.text.strip(), card.find_all('p')[1].text.strip().split(" / "), card.parent.parent["href"]) for card in cards]
    return cards 

def categories(s, options):
    resp = s.get(f"https://{ENDPOINT}/{options.dojo}/challenges")
    soup = bs4.BeautifulSoup(resp.content, "lxml")
    cards = soup.find_all("div", {"class": "card-body"})
    cards = [(card.h4.text.strip(), card.p.text.strip().split(" / "), card.parent.parent["href"]) for card in cards]
    return cards 

def challenges(s, options):
    category = options.category
    if category in challenges_dict:
        return challenges_dict[category]
    resp = s.get(f"https://{ENDPOINT}/{options.dojo}/challenges/{options.category}")
    nonce= re.findall(b"'csrfNonce': \"(.*)\"", resp.content)[0]
    soup = bs4.BeautifulSoup(resp.content, "lxml")
    cards = soup.find_all("div", {"id": "challenges"})[0].find_all("div", {"class": "card"})
    cards = [(card.h4.text.strip(), int(card.find_all("input", {"id": "challenge-id"})[0]["value"])) for card in cards]
    challenges_dict[category] = (cards, nonce)
    return (cards, nonce)

def activate_challenge(s, options, problem, practice=False):
    chals, nonce = challenges(s, options)
    for chal in chals:
        if problem in chal[0]:
            name, chal_id = chal
            resp = s.post(f"https://{ENDPOINT}/pwncollege_api/v1/docker", json = {
                    "challenge_id": chal_id,
                    "practice": practice,
                    "dojo_id": options.dojo
                },
                headers={
                    "CSRF-Token": str(nonce, "UTF-8")
                })
            break
    else:
        print(f"Could not find challenge {problem} for {dojo}/{category}")
        print("Problems found:")
        for chal in chals:
            print(" ", chal[0])
        

def download_challenge(s, options, challenge_id, target_dir):
    activate_challenge(s, options, options.problem, challenge_id)
    p = subprocess.Popen(["scp", "hacker@dojo.pwn.college:/challenge/*", target_dir])
    p.wait()

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")
    subparser.add_parser("login")
    subparser.add_parser("dojos")

    categories_parser = subparser.add_parser("categories")
    categories_parser.add_argument("--dojo", required=True)

    challenges_parser = subparser.add_parser("challenges")
    challenges_parser.add_argument("--dojo", required=True)
    challenges_parser.add_argument("category")

    start_parser = subparser.add_parser("start")
    start_parser.add_argument("--dojo", required=True)
    start_parser.add_argument("category")
    start_parser.add_argument("problem")
    start_parser.add_argument("--practice", action="store_true", default=False)

    download_parser = subparser.add_parser("download")
    download_parser.add_argument("--dojo", required=True)
    download_parser.add_argument("category")
    download_parser.add_argument("problem")
    download_parser.add_argument("target_dir")

    download_all_parser = subparser.add_parser("download-all")
    download_all_parser.add_argument("--dojo", required=True)
    download_all_parser.add_argument("category")
    download_all_parser.add_argument("target_dir")
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
    elif options.command == "dojos":
        for dojo in dojos(s, options):
            name, (solved, total), href = dojo
            print(f"{name} {solved} / {total} [{href}]")
    elif options.command == "categories":
        for category in categories(s, options):
            name, (solved, total), href = category
            print(f"{name} {solved} / {total} [{href}]")
    elif options.command == "challenges":
        chals, nonce = challenges(s, options)
        for challenge in chals:
            print(challenge)
    elif options.command == "start":
        activate_challenge(s, options, options.problem, options.practice)
    elif options.command == "download":
        download_challenge(s, options, options.problem, options.target_dir)
    elif options.command == "download-all":
        chals, nonce = challenges(s, options)
        for (problem, id) in chals:
            download_challenge(s, options, problem, options.target_dir)
    else:
        print(options)
        print("No command specified!")

if __name__=="__main__":
    main()
