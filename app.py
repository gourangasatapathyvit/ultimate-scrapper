import os
from bs4 import BeautifulSoup
import re
import cloudscraper
import requests
import json
from flask import Flask, request, Response
from dotenv import load_dotenv
load_dotenv()


sitesAvailable = [{"id": 1, "name": "1337x"}, {"id": 2, "name": "yifytorrent"}]
scraper = cloudscraper.create_scraper(delay=6, browser='chrome')

home = [
    {"route_id": 1, "route_name": "Home", "route_url": "/",
        "info": "all available api endpoints"},
    {"route_id": 2, "route_name": "Torrent List", "route_url": "/torrents",
        "info": "it listouts all details regarding queries"},
    {"route_id": 3, "route_name": "Torrent Data", "route_url": "/magnet",
        "info": "generate magnet url of particular item"},
    {"route_id": 4, "route_name": "Sites",
        "route_url": "/sites", "info": "all host address"},
]


def yifytorrent(search_key, year):
    URL = f"https://yifytorrent.unblockit.boo/search/{search_key}/p-1/all/all/"
    response = scraper.get(URL).content
    soup = BeautifulSoup(response, 'lxml')
    soupRes = soup.find_all("article", {'class': 'img-item'})
    yifyList = []

    for i in soupRes:
        urlContent = f"https://yifytorrent.unblockit.boo{i.find('a', {'class': 'movielink'})['href']}"
        poster = f"https://yifytorrent.unblockit.boo{i.find('img',{'class':'poster-thumb'})['src']}"

        if str(year) in str(i.find('a', {'class': 'movielink'}).text):
            yifyList.append(
                {
                    "name": i.find('a', {'class': 'movielink'}).text,
                    "url": urlContent,
                    "poster": poster,
                    "uploader": "yify",
                    "source": "yify"
                }
            )

    return yifyList


def getTorrentsList(search_key):
    res = requests.get(f"{os.getenv('host')}/search?query={search_key}")
    finalData = []

    for i in res.json()['results']:
        eachData = {}
        eachData['metaData'] = [
            i
        ]
        eachData['YIFY'] = yifytorrent(i['title'].lower(), i['year'])

        if (True):
            torrentData = []
            URL = f"https://1337x.unblockit.boo/search/{i['title']} {i['year']}/1/"
            response = scraper.get(URL).content
            soup = BeautifulSoup(response, 'lxml')
            results = soup.find('tbody')
            results = soup.find_all('tr')
            if (len(results) > 0):
                results.pop(0)

            for i in results:
                cols = i.find_all("td")
                col1 = cols[0].find_all("a")[1]
                name = col1.text
                urlContent = "https://1337x.unblockit.boo" + col1['href']
                torrentData.append(
                    {
                        "name": name,
                        "url": urlContent,
                        "uploader": cols[5].text,
                        "size": f'{cols[4].text.split("GB",1)[0]}GB',
                        "uploaded at": cols[3].text,
                        "source": "1337x"
                    }
                )
            eachData['1337X'] = torrentData
        finalData.append(eachData)

    return finalData


def gettorrentdata(link, imdbPath):
    itemDetails = []
    res = requests.get(f"{os.getenv('host')}{imdbPath}")
    itemDetails.append(res.json())
    alldataLinks = {}
    response = scraper.get(link).content
    soup = BeautifulSoup(response, 'lxml')
    magnet = soup.find("a", href=re.compile(
        r'[magnet]([a-z]|[A-Z])\w+'), class_=True).attrs["href"]
    adtionalMetaData = soup.find_all('ul', {'class': 'list'})
    adtionalMetaDataLeft = adtionalMetaData[1].find_all('li')
    adtionalMetaDataRight = adtionalMetaData[2].find_all('li')
    uflixLink = f"https://uflix.cc/search?keyword={soup.find('a', href=re.compile(r'/movie/')).text}"

    alldataLinks["magnet"] = magnet
    alldataLinks["webTor"] = f'https://webtor.io/show?magnet={magnet}'
    alldataLinks["uflix"] = uflixLink if uflixLink != None else "Not Available"
    alldataLinks["metaData"] = {
        "Category": adtionalMetaDataLeft[0].find('span').text,
        "language": adtionalMetaDataLeft[2].find('span').text,
        "uploader": adtionalMetaDataLeft[4].find('span').text,
        "size": adtionalMetaDataLeft[3].find('span').text,
        "seeds": adtionalMetaDataRight[3].find('span').text,
        "leeches": adtionalMetaDataRight[4].find('span').text,

    }
    itemDetails.append(alldataLinks)
    return itemDetails


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

    with open("blocklist.txt", "r") as file:
        blocklist = file.read().split("\n")
        if (search_key.strip().lower() in blocklist) or search_key is None or search_key == "":
            return Response(json.dumps([{'result': 'no data available'}]))

    return Response(
        json.dumps(getTorrentsList(search_key)), mimetype="application/json"
    )


@app.route("/magnet", methods=["GET"])
def getTorrentData():
    link = request.args.get("link")
    imdbPath = request.args.get("a")
    if link is None or link == "":
        return Response(json.dumps([]))
    return Response(json.dumps(gettorrentdata(link, imdbPath)), mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
