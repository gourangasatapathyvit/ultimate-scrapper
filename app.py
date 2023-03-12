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
        # response = scraper.get(urlContent).content
        # dataPage = BeautifulSoup(response, 'lxml')
        # magnetData = gettorrentdata(urlContent)
        # adtionalMetaData = dataPage.find_all('ul', {'class': 'list'})
        # adtionalMetaData = adtionalMetaData[1].find_all('li')
        # uflixLink = dataPage.find('a', id= 'l837afe5cf495ce3e74d6b938f950f625a02013a8')

       
        data.append(
            {
                "name": name,
                "url": urlContent,
                # "magnetUrl": magnetData['magnet'],
                # "webTor":f'https://webtor.io/show?magnet={ magnetData["magnet"]}',
                # "uflix":uflixLink['href'] if uflixLink != None else "Not Available",
                "seeds": cols[1].text,
                "leeches": cols[2].text,
                # "metaData": {
                #     "uploader": cols[5].text,
                #     "size": f'{cols[4].text.split("GB",1)[0]}GB',
                #     "date": cols[3].text,
                #     "itemType":adtionalMetaData[0].find('span').text,
                #     "language":adtionalMetaData[2].find('span').text

                # }
            }
        )
    return data


def gettorrentdata(link):
    data = {}
    response = scraper.get(link).content
    soup = BeautifulSoup(response, 'lxml')
    magnet = soup.find("a", href=re.compile(r'[magnet]([a-z]|[A-Z])\w+'), class_=True).attrs["href"]
    data["magnet"] = magnet
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
