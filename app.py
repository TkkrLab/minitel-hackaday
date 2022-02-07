#!/usr/bin/env python3

import requests, sys, time
from html.parser import HTMLParser

import serial
import pynitel
from bs4 import BeautifulSoup
import requests
import sys
import json
import re

class MyHTMLParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super(MyHTMLParser, self).__init__( *args, **kwargs)
        self.output = ""

    def getOutput(self):
        return self.output

    def resetOutput(self):
        self.output = ""

    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.output += "\n\n========================\n";
        elif tag == 'p':
            self.output += "\n";

    def handle_data(self, data):
        self.output += data

parser = MyHTMLParser(convert_charrefs=False)

def msg(title, text):
    global m
    m.resetzones()
    m.home()
    m.inverse()
    m._print(title + "\r\n")
    m.inverse(False)
    text = text.replace("\n","\r\n")
    toPrint = text
    while len(toPrint) > 0:
        line = toPrint[:40]
        m._print(line)
        if len(line) < 40:
            m._print("\r\n")
        toPrint = toPrint[40:]

def msg_paginated(title, text):
    global m
    text = text.replace("\r","")
    lines_raw = text.split("\n")
    lines_formatted = []
    for i in range(len(lines_raw)):
        data = lines_raw[i]
        while len(data) > 0:
            line = data[:40]
            lines_formatted.append(line)
            data = data[40:]
            
    lines = len(lines_formatted)
    
    pages = []
    page = []
    line_count = 0
    for i in range(len(lines_formatted)):
        page.append(lines_formatted[i])
        line_count+=1
        if (line_count > 22):
            line_count = 0
            pages.append(page)
            page = []
    pages.append(page)
    
    current_page = 0
    
    while True:
        m.resetzones()
        m.home()
        m.inverse()
        if (len(title) > 36):
            title = title[:33] + "..."
        title += str(current_page + 1)+"/"+str(len(pages))
        m._print(title[:40])
        if (len(title) < 40):
            m._print("\r\n")
        m.inverse(False)
        page = pages[current_page]
        for i in range(len(page)):
            m._print(page[i])
            if len(page[i]) < 40:
                m._print("\r\n")
        
        choice = 0
        while True:
            (choice, function) = m.input(0, 1, 0, '')
            if function == m.annulation:
                return
            if function == m.guide:
                return
            if function == m.retour:
                if current_page > 0:
                    current_page -= 1
                    break
            if function == m.suite:
                if current_page < (len(pages) - 1):
                    current_page += 1
                    break

def fetchTitles():
    url = "https://hackaday.com/wp-json/wp/v2/posts?_fields[]=id&_fields[]=title"
    r = requests.get(url)
    data = r.json()
    r.close()
    titles = []
    for i in data:
        titles.append((i['id'], i['title']['rendered']))
    return titles

def fetchDocument(id):
    url = "https://hackaday.com/wp-json/wp/v2/posts/{}?_fields[]=content".format(id)
    r = requests.get(url)
    data = r.json()
    r.close()
    return data['content']['rendered']

def menu():
    msg("Hack-a-day reader", "Fetching titles...")
    titles = fetchTitles()
    list = []
    for i in titles:
        list.append(i[1])
    global m
    m.resetzones()
    m.home()
    m.inverse()
    m._print("Hack-a-day reader - select article\r\n")
    m.inverse(False)
    for i in range(len(titles)):
        m.inverse()
        m._print("{: >2d}".format(i))
        m.inverse(False)
        m._print(" ")
        toPrint = re.sub("&.*?;", "", titles[i][1])
        first = True
        while len(toPrint) > 0:
            if not first:
                m._print("   ")
            first = False
            line = toPrint[:37]
            m._print(line)
            if len(line) < 37:
                m._print("\r\n")
            toPrint = toPrint[37:]
    done = False
    choice = 0
    while not done:
        (choice, function) = m.input(0, 1, 1, '')
        if function == m.correction:
            continue
        if function == m.annulation:
            return (-1,"")
        if function == m.envoi:
            done = True
        print("Choice", choice, function)
        try:
            choice = int(choice)
            if choice >= len(titles):
                print("Invalid choice")
                done = False
        except:
            print("NaN")
            done = False
    return titles[choice]

def renderDocument(title, text):
    parser.resetOutput()
    parser.reset()
    parser.feed(text)
    msg_paginated(title, re.sub("&.*?;", "", parser.output))

def init():
    global m
    m = pynitel.Pynitel(serial.Serial('/dev/ttyACM0', 1200, parity=serial.PARITY_EVEN, bytesize=7, timeout=2))


def showLogo(logo):
    m.resetzones()
    m.home()
    m._print(logo.replace("\r","").replace("\n",""))
    m.inverse()
    m._print("\r\n")
    m._print("Hack-a-day reader for Minitel           ")
    m.inverse(False)
    m._print("A TkkrLab project :D\r\n")
    (choice, function) = m.input(0, 1, 1, '')

def main():
    with open("logo", "r") as f:
        logo = f.read()
    init()
    
    showLogo(logo)
    
    while True:
        id, title = menu()
        if id < 0:
            showLogo(logo)
        else:
            renderDocument(title, fetchDocument(id))

main()
