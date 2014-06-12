#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
import json
import urllib
from workflow import Workflow
from bs4 import BeautifulSoup

GREEK_ALPHABET = [
    "α", "β", "γ", "δ", "ε", 
    "ζ", "η", "θ", "ι", "κ", 
    "λ", "μ", "ν", "ξ", "ο", 
    "π", "ρ", "σ", "ς", "τ", 
    "υ", "φ", "χ", "ψ", "ω", 
    "Α", "Β", "Γ", "Δ", "Ε", 
    "Ζ", "Η", "Θ", "Ι", "Κ", 
    "Λ", "Μ", "Ν", "Ξ", "Ο", 
    "Π", "Ρ", "Σ", "Τ", "Υ", 
    "Φ", "Χ", "Ψ", "Ω"
]

def unify(obj, encoding='utf-8'):
    """Detects if object is a string and if so converts to unicode"""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def get_language(obj):
    """Determines language of input text"""
    if len([c for c in obj if c in GREEK_ALPHABET]) > 0:
        return 'greek'
    else:
        return 'latin'

def scrape_perseus(query, lang):
    """Extracts all relevant data from Perseus parser"""
    base_url = "http://www.perseus.tufts.edu/hopper/morph?l="
    perseus_url = base_url + query + "&la=" + lang
    html = urllib.urlopen(perseus_url).read()
    soup = BeautifulSoup(html)
    parse_results = soup.find('div', {"id" : "main_col"})
    parse_items = parse_results.find_all('div', {"class" : "analysis"})

    _data = []
    for item in parse_items:
        dct = {}
        if item.h4.string != None:
            dct['lemma'] = item.h4.string.strip()
        else:
            dct['lemma'] = 'missing value'

        if item.span.string != None:
            dct['definition'] = item.span.string.strip()
        else:
            dct['definition'] = 'missing value'

        dct['parsing_data'] = [p.string.strip() 
                        for p in item.table.find_all('td', {'class': None}) 
                        if p.get('style') == None]
        dct['links'] = [(u.get('id').replace('-link', ''), u.string)
                for u in item.find_all('a')
                if u.get('id') != None]
        _data.append(dct)
    return _data

def scrape_chicago(query, lang):
    """Extracts all relevant data from Chicago parser"""
    base_url = "http://perseus.uchicago.edu/perseus-cgi/morph.pl?token="
    chicago_url = base_url + query + "&lang=" + lang
    html = urllib.urlopen(chicago_url).read()
    soup = BeautifulSoup(html)
    lemmas = soup.find_all('table', {'class': 'lemmacontainer'})
    
    _data = []
    for tbl in lemmas:
        dct = {}
        dct['lemma'] = tbl.tr.th.string
        dct['logeion'] = tbl.a.get('href')
        dct['definition'] = tbl.find('th', {'class': 'shortdef'}).string
        dct['token'] = tbl.find('td', {'class': 'token'}).string
        #parsing = [p.string for p in tbl.find_all('td', {'class': 'code'})]
        _data.append(dct)
    return _data



def main(wf):
    """Parse input"""
    
    query = wf.args[0]
    #query = 'οἴου'
    input_ = unify(query)
    lang = get_language(input_)
    html_query = urllib.quote(input_.encode('utf-8'))

    #def wrapper():
    #    return scrape_perseus(html_query, lang)

    #data = wf.cached_data('data', wrapper, max_age=60)

    data = scrape_perseus(html_query, lang)

    json_cache = json.dumps(data, 
                            sort_keys=True, 
                            indent=4, 
                            separators=(',', ': '))

    with open(wf.cachefile("parse_cache.json"), 'w') as file_:
        file_.write(json_cache.encode('utf-8'))
        file_.close()


    for item in data:
        sub = item['lemma'] + ' :: ' + item['definition']
        for parsings in item['parsing_data']:
            args = json.dumps(parsings)
            wf.add_item(parsings, 
                        sub,
                        arg=args,
                        valid=True)
    
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
