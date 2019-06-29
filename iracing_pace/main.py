import requests
import re
import urllib.parse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import sys
from config import credentials

SUBSESSION = 27571384
FASTEST_DELTA = 5
MIN_POSITION = 10
URL_IRACING_LOGIN = 'https://members.iracing.com/membersite/Login'
URL_API = f"https://members.iracing.com/membersite/member/EventResult.do?&subsessionid={SUBSESSION}"
NIMROD_URL = 'https://www.nimrod-messenger.io/api/v1/message'

def main():
    with requests.session() as s:
        s.post(URL_IRACING_LOGIN, data=credentials)
        text = s.get(URL_API).text
        found = re.findall(r"var\sresultOBJ\s*=\s*{([\S\s]*?simSesName:\"RACE\"[\S\s]*?)};", text)
        cleaned = [clean(x) for x in found]
        drivers = [make_dict(x) for x in cleaned]
        grid = {}
        
        fastest_time = np.inf;

        for driver in drivers:
            name = get_name(driver['displayName'])
            irating = driver['newiRating']
            custid = driver['custid']
            pos = driver['finishPos']
            laps_url = f"https://members.iracing.com/membersite/member/GetLaps?&subsessionid={SUBSESSION}&groupid={custid}&simsesnum=0"
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
        if int(info['pos']) <= MIN_POSITION:
            *first, last = name.split(" ")
            for lap in info['laps']:
                if lap < fastest_time + FASTEST_DELTA:
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
    sys.exit(main())