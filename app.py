from bs4 import BeautifulSoup
import re
import cloudscraper
import requests
import json
from flask import Flask, request, Response

sitesAvailable = [{"id": 1, "name": "1337x"}]
scraper = cloudscraper.create_scraper(delay=6, browser='chrome')

home = [
    {"route_id": 1, "route_name": "Home", "route_url": "/", "info": "all available api endpoints"},
    {"route_id": 2, "route_name": "Torrent List", "route_url": "/torrents","info": "it listouts all details regarding queries"},
    {"route_id": 3, "route_name": "Torrent Data", "route_url": "/magnet","info": "generate magnet url of particular item"},
    {"route_id": 4, "route_name": "Sites", "route_url": "/sites","info": "all host address"},
]


def getTorrentsList(search_key):
    URL = f"https://1337x.unblockit.boo/search/{search_key}/1/"
    response = scraper.get(URL).content
    soup = BeautifulSoup(response, 'lxml')
    data = []
    results = soup.find('tbody')
    results = soup.find_all('tr')
    if len(results) > 10:
        length = 11
    else:
        length = len(results)

    for i in range(1, length):
        cols = results[i].find_all("td")
        col1 = cols[0].find_all("a")[1]
        name = col1.text
        urlContent = "https://1337x.unblockit.boo" + col1['href']

        data.append(
            {
                "name": name,
                "url": urlContent,
                "seeds": cols[1].text,
                "leeches": cols[2].text,
                "uploader": cols[5].text,
                "size": f'{cols[4].text.split("GB",1)[0]}GB',
                "uploaded at": cols[3].text,
            }
        )
    return data


def gettorrentdata(link):
    data = {}
    response = scraper.get(link).content
    soup = BeautifulSoup(response, 'lxml')
    magnet = soup.find("a", href=re.compile(r'[magnet]([a-z]|[A-Z])\w+'), class_=True).attrs["href"]
    adtionalMetaData = soup.find_all('ul', {'class': 'list'})
    adtionalMetaDataLeft = adtionalMetaData[1].find_all('li')
    adtionalMetaDataRight = adtionalMetaData[2].find_all('li')
    uflixLink = f"https://uflix.cc/search?keyword={soup.find('a', href=re.compile(r'/movie/')).text}"

    data["magnet"] = magnet
    data["webTor"]=f'https://webtor.io/show?magnet={magnet}'
    data["uflix"]=uflixLink if uflixLink != None else "Not Available"
    data["metaData"] = {
        "Category":adtionalMetaDataLeft[0].find('span').text,
        "language":adtionalMetaDataLeft[2].find('span').text,
        "uploader":adtionalMetaDataLeft[4].find('span').text,
        "size":adtionalMetaDataLeft[3].find('span').text,
        "seeds": adtionalMetaDataRight[3].find('span').text,
        "leeches": adtionalMetaDataRight[4].find('span').text,

    }
    return data


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return Response(json.dumps(home), mimetype="application/json")


@app.route("/sites", methods=["GET"])
def getSites():
    return Response(json.dumps(sitesAvailable), mimetype="application/json")


@app.route("/torrents", methods=["GET"])
def getTorrents():
    search_key = request.args.get("key")
    print(search_key)
    if search_key is None or search_key == "":
        return Response(json.dumps([]))
    return Response(
        json.dumps(getTorrentsList(search_key)), mimetype="application/json"
    )


@app.route("/magnet", methods=["GET"])
def getTorrentData():
    link = request.args.get("link")
    if link is None or link == "":
        return Response(json.dumps([]))
    return Response(json.dumps(gettorrentdata(link)), mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=True)
