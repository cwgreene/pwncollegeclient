import argparse
import bs4
import requests
import os
import colorama

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    options = parser.parse_args()
    resp = requests.get("https://dojo.pwn.college/scoreboard")
    soup = bs4.BeautifulSoup(resp.content, "lxml")

    results = []
    for row in soup.find_all("a"):
        if "/users" in row.get("href"):
            row = row.parent.parent.find_all("td")
            emblem = os.path.basename(row[0].img["src"])
            name = row[1].text.strip()
            score = row[2].text.strip()
            results.append((score, name, emblem))
    logos = {"hacker.png": "💻", "fork.png": "♆"}
    red = colorama.Fore.RED
    yellow = colorama.Fore.YELLOW
    reset = colorama.Fore.WHITE
    for i, (score, name, emblem) in enumerate(results[:options.count], 1):
        print(f"{i}. {yellow + name + reset} {score} {red+logos.get(emblem, 'OTHER')+reset}")

if __name__ == "__main__":
    main()
