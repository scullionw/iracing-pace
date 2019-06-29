import requests
import re
import urllib.parse
import pandas as pd
import seaborn as sns
import numpy as np
import sys
from config import credentials
import argparse


URL_IRACING_LOGIN = 'https://members.iracing.com/membersite/Login'

def main(args):
    event_page = f"https://members.iracing.com/membersite/member/EventResult.do?&subsessionid={args.subsession}"

    with requests.session() as s:
        s.post(URL_IRACING_LOGIN, data=credentials)
        text = s.get(event_page).text
        found = re.findall(r"var\sresultOBJ\s*=\s*{([\S\s]*?)};", text)
        cleaned = [clean(x) for x in found]
        drivers = [make_dict(x) for x in cleaned]
        drivers = [driver for driver in drivers if driver['simSesName'] == "\"RACE\""]
        
        grid = {}
        fastest_time = np.inf

        for driver in drivers:
            name = get_name(driver['displayName'])
            irating = driver['newiRating']
            custid = driver['custid']
            pos = driver['finishPos']
            laps_url = f"https://members.iracing.com/membersite/member/GetLaps?&subsessionid={args.subsession}&groupid={custid}&simsesnum=0"
            response = s.get(laps_url)

            laps = response.json()['lapData']
            lap_arr = []
            
            for a, b in zip(laps, laps[1:]):
                delta = (b['ses_time'] - a['ses_time']) / 10000
                if delta < fastest_time:
                    fastest_time = delta
                lap_arr.append(delta)
                
            grid[name] = {'irating': irating, 'custid': custid, 'pos': pos, 'laps': lap_arr}

    dataset = []
    for name, info in grid.items():
        if int(info['pos']) <= args.maxpos:
            *first, last = name.split(" ")
            for lap in info['laps']:
                if lap < fastest_time + args.maxdelta:
                    dataset.append({'Driver': f"{last} [{info['irating']}]", 'Lap Time': lap})

    df = pd.DataFrame(dataset)  

    sns.set(style="whitegrid")
    ax = sns.swarmplot(x="Driver", y="Lap Time", data=df)
    for item in ax.get_xticklabels():
        item.set_rotation(90)

    figure = ax.get_figure()    
    figure.savefig('pace.png', bbox_inches='tight', dpi=400)


def clean(text):
    text = text.replace('\n', '')
    text = text.replace('\t', '')
    text = text.replace('\r', '')
    text = text.replace("\'", "\"")
    return text

def make_dict(s):
    pairs = [x.split(":") for x in s.split(",")]
    drivers = {}
    for pair in pairs:
        if len(pair) == 2:
            drivers[pair[0]] = pair[1]
    return drivers

def get_name(s):
    start = s.find("(")
    end = s.find(")")
    name = s[start+2:end-1]
    name = name.replace("+", " ")
    return urllib.parse.unquote(name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyse pace from iracing race session')

    parser.add_argument('subsession', type=str, help='Subsession ID')
    parser.add_argument('--maxpos', type=int, help='Minimum race position', default=5)
    parser.add_argument('--maxdelta', type=int, help='Maximum lap time delta to fastest lap', default=10)

    sys.exit(main(parser.parse_args()))