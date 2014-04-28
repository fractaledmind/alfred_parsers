#!/usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

import sys
import json
import urllib
import subprocess
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

def prettify_parsing(text):
    """Prepares pretty string of parsing data"""
    parts = text.split(' ')
    
    txt = []
    for key, list_ in SYNTAX.items():
        for item in parts:
            if item in list_:
                header = key.title()[:-1] + ': '
                txt += [header + item]
                parts.remove(item)
    if len(parts) > 0:
        info = ', '.join(parts)
        txt += ['Syntax: ' + info]
    return '\n'.join(sorted(txt, reverse=True))

def prettify_info(obj):
    """Prepares pretty string of lemma information"""
    txt = ['Definition:' + obj['definition']]
    txt += ['Lemma: ' + obj['lemma']]
    for link in obj['links']:
        base_url = 'http://www.perseus.tufts.edu/hopper/text?doc='
        html_link = urllib.quote(link[0])
        url = base_url + html_link
        md_link = '\t+ [' + link[1] + '](' + url + ')'
        txt += [md_link]
    return '\n'.join(sorted(txt, reverse=True))



def main(wf):

    input_ = json.loads(wf.args[0])
    #input_ = json.loads('["noun sg fem acc"]')

    with open(wf.cachefile("parse_cache.json"), 'r') as file_:
        data = json.load(file_)
        file_.close()

    for item in data:
        for parsings in item['parsing_data']:
            if parsings == input_:
                pretty_parse = prettify_parsing(parsings)
                pretty_info = prettify_info(item)
                output = pretty_parse + '\n\n' + pretty_info

                set_clipboard(output)
                print "Parsing Data"
                


if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
