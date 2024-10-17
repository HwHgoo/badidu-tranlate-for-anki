import requests
import time
import json
import fileinput

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
headers = {
    'ua' : ua,
}

class trans_request:
    domain = 'common'
    lan_from = 'en'
    lan_to = 'zh'
    needPhonetic = True
    milliTimestamp = 0
    def __init__(self, query: str) -> None:
        self.query = query
        self.milliTimestamp = int(time.time_ns() / 1000)
    
    def toDict(self):
        return {
            'domain': self.domain,
            'from': self.lan_from,
            'to': self.lan_to,
            'needPhonetic': self.needPhonetic,
            'milliTimestamp': self.milliTimestamp,
            'query': self.query
        }

url_translate = 'https://fanyi.baidu.com/ait/text/translate'

class translator:
    session = requests.Session()

def retriveSimpleMeans(data: dict) -> tuple:
    simplemeaning = data['simple_means']
    symbol = simplemeaning['symbols'][0]
    ph_am = symbol['ph_am']
    ph_en = symbol['ph_en']

    parts = symbol['parts']
    meanings = list(map(lambda p: f'{p['part']} \n {";".join(p['means'])}', parts))
    meanings = "\n".join(meanings)
    tags = simplemeaning['tags']
    tags = list(filter(lambda x: x != "", tags['core'] + tags['other']))

    return (meanings, tags, (ph_am, ph_en))

def retriveCollins(data: dict):
    collins = data['collins']
    frequence = collins['frequence']
    entry = collins['entry']
    means = list(filter(lambda x: x['type'] == 'mean' and len(x['value']) and x['value'][0]['def'] and len(x['value'][0]['posp']), entry))
    meanings = [
        f'\n{value['posp'][0]['label']} {value['tran']} \n {value['def']} \n {value['mean_type'][0]['example'][0]['ex'] if len(value['mean_type']) and len(value['mean_type'][0]['example']) else ""} \n'
        for x in means
        for value in [x['value'][0]]
    ]
    meanings = "\n".join(meanings)
    return (frequence, meanings)



def translate(query: str) -> dict:
    session = requests.Session()
    b =trans_request(query)
    with session.post(url=url_translate, json=b.toDict(), headers=headers, stream=True) as rsp:
        for line in rsp.iter_lines():
            if line and line != b'event: message':
                l = json.loads(line[5:])
                data = l['data']
                if not data:
                    continue
                msg = data['message']
                if msg == "获取词典成功":
                    return data['dictResult']


if __name__ == "__main__":
    checked = set()
    with open("words.csv", 'w+t', encoding='utf-8') as f:
        for word in fileinput.input():
            word = word.rstrip()
            if word == "_exit":
                break
            if word in checked:
                continue
            result = translate(word)
            meanings, tags, phs = retriveSimpleMeans(result)
            collins_frequence, collins_meanings = retriveCollins(result)
            card = f'{word}|{phs}|{meanings}|{tags}|{collins_frequence}\n{collins_meanings}'
            card = card.replace("\n", "<br>")
            f.write(card)
            f.flush()