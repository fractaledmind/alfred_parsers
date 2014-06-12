#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import re
import sys
import json
import urllib
import subprocess
from bs4 import BeautifulSoup
from workflow import Workflow

SYNTAX = {
    'TYPES': ["noun", "verb", "part", "adj", "adv", "prep", "pron", 
                "conj", "partic", "article", "irreg", "exclam"],
    'NUMBERS': ["sg", "pl", "dual"],
    'GENDERS': ["fem", "masc", "neut"],
    'CASES': ["nom", "voc", "acc", "gen", "dat"],
    'PERSONS': ["1st", "2nd", "3rd"],
    'TENSES': ["pres", "fut", "imperf", "perf", "plup", "futperf", "aor"],
    'MOODS': ["subj", "ind", "imperat", "inf", "opt"],
    'VOICES': ["act", "pass", "mp"]
}

LEXICON_HIERARCHY = [
    'Middle Liddell',
    'Elem. Lewis',
    'LSJ',
    'Lewis & Short',
    'Slater',
    'Autenrieth'
]

#################################################################
# Applescript Functions
#################################################################

def unify(obj, encoding='utf-8'):
    """Detects if object is a string and if so converts to unicode"""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def _applescriptify(text):
    """Replace double quotes in text"""
    return text.replace('"', '" + quote + "')

def set_clipboard(data):
    """Set clipboard to ``data``""" 
    scpt = """
        set the clipboard to "{0}"
    """.format(_applescriptify(data))
    subprocess.call(['osascript', '-e', scpt])


#################################################################
# Prettify Parsing Data
#################################################################

def prettify_parsing(text):
    """Prepares pretty string of parsing data"""
    parts = text.split(' ')
    
    txt = []
    for key, list_ in SYNTAX.items():
        for item in parts:
            if item in list_:
                header = key.title()[:-1] + ':\t'
                txt += [header + item]
                parts.remove(item)
    if len(parts) > 0:
        info = ', '.join(parts)
        txt += ['Syntax:\t' + info]
    return '\n'.join(sorted(txt, reverse=True))

def prettify_info(obj):
    """Prepares pretty string of lemma information"""
    txt = ['Definition:\t' + obj['definition']]
    txt += ['Lemma:\t' + obj['lemma']]
    #for link in obj['links']:
    #    base_url = 'http://www.perseus.tufts.edu/hopper/text?doc='
    #    html_link = urllib.quote(link[0])
    #    url = base_url + html_link
    #    md_link = '\t+ [' + link[1] + '](' + url + ')'
    #    txt += [md_link]
    return '\n'.join(sorted(txt, reverse=True))


#################################################################
# Prettify Lexicon Data
#################################################################

def scrape_lexicon(_link):
    """Retrieve text of lexicon entry for chosen term"""
    base_url = 'http://www.perseus.tufts.edu/hopper/text?doc='
    html_link = urllib.quote(_link)
    _url = base_url + html_link
    html = urllib.urlopen(_url).read()
    soup = BeautifulSoup(html)
    _results = soup.find('div', {"class" : "text_container en"})
    _sections = _results.find_all('div', {"class" : "lex_sense"})
    
    sections_lst = []
    for item in _sections:
        _uni = unify(str(item))
        clean_tags = re.sub(r"<[^<>]+>", "", _uni)
        clean_outline = re.sub(r"(^\w+\.)(?!\s)", "\\1 ", clean_tags)
        clean_spaces = re.sub(r"\s{2,}", " ", clean_outline)
        clean_sub_sections = re.sub(";", "\n", clean_spaces)
        clean_sub_sections = re.sub("(—)", "\n\n\\1 ", clean_sub_sections)

        sections_lst.append(clean_sub_sections)
    return sections_lst

def get_best_lexicon(data):
    """Determine while lexicon to scrape"""
    for lex in LEXICON_HIERARCHY:
        _res = [x[0] for x in data['links'] if lex in x]
        if len(_res) > 0:
            return [_res[0], lex]



def main(wf):
    """Primary action"""
    action_ = wf.args[1]
    input_ = json.loads(wf.args[0])
    #input_ = json.loads('["noun sg fem acc"]')

    with open(wf.cachefile("parse_cache.json"), 'r') as file_:
        data = json.load(file_)
        file_.close()

    for item in data:
        for parsings in item['parsing_data']:
            if parsings == input_:
                if action_ == 'parse':
                    pretty_parse = prettify_parsing(parsings)
                    pretty_info = prettify_info(item)
                    output = pretty_parse + '\n\n' + pretty_info
                    set_clipboard(output)
                    print output.encode('utf-8')
                
                elif action_ == 'lexicon':
                    lex = get_best_lexicon(item)
                    sects = scrape_lexicon(lex[0])
                    output = '# ' + lex[1] + '\n\n' + '\n\n'.join(sects)
                    set_clipboard(output)
                    print output.encode('utf-8')
                
                break

if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
