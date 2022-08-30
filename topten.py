import argparse
import requests
import os
import colorama
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    options = parser.parse_args()
    count = 0
    i = 1
    while count < options.count:
        resp = requests.get(f"https://dojo.pwn.college/pwncollege_api/v1/scoreboard/cse466/dojo/{i}")
        scores = json.loads(resp.content)["page_standings"]
        cur_count = count
        count += len(scores)
        if count > options.count:
            diff = count - options.count
            scores = scores[:-diff]
        red = colorama.Fore.RED
        yellow = colorama.Fore.YELLOW
        reset = colorama.Fore.WHITE
        logos = {"hacker.png": "💻", "fork.png": "♆"}
        for score in scores:
            logo = "♆" if "fork.png" in score["symbol"] else "💻" 
            print(f"{i}. {yellow + score['name'] + reset} {score['score']} {red}{logo}{reset}")
            i += 1

if __name__ == "__main__":
    main()
