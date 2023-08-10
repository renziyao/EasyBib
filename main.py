import requests
import os
import bibtexparser
import difflib
import functools
import warnings
from tqdm import tqdm

warnings.filterwarnings(action='ignore')

keep_field = {
    'article': ['title', 'author', 'journal', 'year', 'volume', 'number', 'pages'],
    'inproceedings': ['title', 'author', 'booktitle', 'year', 'pages'],
    'booklet': [],
    'conference': [],
    'inbook': [],
    'incollection': ['title', 'author', 'booktitle', 'year', 'series', 'volume', 'pages'],
    'manual': [],
    'mastersthesis': [],
    'misc': [],
    'proceedings': [],
    'techreport': [],
    'unpublished': [],
}

venue_field = {
    'article': 'journal',
    'inproceedings': 'booktitle',
    'incollection': 'booktitle',
}


def get_bibtex_from_dblp(item):
    item_bib_str = requests.get(item["info"]["url"] + ".bib?param=1", verify=False).text
    item_bib = bibtexparser.parse_string(item_bib_str).entries[0]
    # update venue name
    if item["info"]["type"] in ["Journal Articles", "Conference and Workshop Papers"]:
        kw = {"q": "/".join(item["info"]["key"].split("/")[:2]), "format": "json", "h": 1000}
        venue = requests.get("https://dblp.org/search/venue/api", params=kw, verify=False).json()
        for item_venue in venue["result"]['hits']['hit']:
            if item_venue["info"]["url"] == 'https://dblp.org/db/' + "/".join(item["info"]["key"].split("/")[:2]) + "/":
                venue_name = item_venue['info']['venue']
                if 'acronym' in item_venue['info']:
                    venue_name = venue_name.replace(
                        ' (%s)' % item_venue['info']['acronym'],
                        ''
                    )
                venue_name = venue_name.split(",")[0]
                item_bib.fields_dict[venue_field[item_bib.entry_type]].value = venue_name
    # print(item_bib)
    return item_bib


def remove_useless_field(item_bib):
    item_bib.fields = [field for field in item_bib.fields if field.key in keep_field[item_bib.entry_type]]


def search_bibtex(title):
    kw = {"q": title, "format": "json"}
    res = requests.get("https://dblp.org/search/publ/api", verify=False, params=kw).json()
    
    if res['result']['hits']['@total'] == "0":
        raise Exception("not found: %s" % title)

    def cmp(x, y):
        a = difflib.SequenceMatcher(None, title, x['info']['title']).ratio()
        b = difflib.SequenceMatcher(None, title, y['info']['title']).ratio()
        if a != b:
            return a - b
        informal = 'Informal and Other Publications'
        if x['info']['type'] == informal and y['info']['type'] != informal:
            return -1
        if x['info']['type'] != informal and y['info']['type'] == informal:
            return 1
        return 0
    item = sorted(res['result']['hits']['hit'], key=functools.cmp_to_key(cmp), reverse=True)
    item = item[0]
    title_threshold = difflib.SequenceMatcher(None, title, item['info']['title']).ratio()
    if title_threshold > 0.9:
        return item
    raise Exception("not found: %s, first one: %s" % (title, item['info']['title']))


def beautify(bibtex_str):
    library = bibtexparser.parse_string(bibtex_str)
    print(f"Parsed {len(library.blocks)} blocks, including:"
          f"\n\t{len(library.entries)} entries"
          f"\n\t{len(library.comments)} comments"
          f"\n\t{len(library.strings)} strings and"
          f"\n\t{len(library.preambles)} preambles")
    formatted_bibtex = bibtexparser.Library()
    for entry in tqdm(library.entries):
        try:
            title = ' '.join(entry["title"].split()).replace("\n", "")
            item = search_bibtex(title)
            item = get_bibtex_from_dblp(item)
            remove_useless_field(item)
            item.key = entry.key
            formatted_bibtex.add(item)
        except Exception as e:
            remove_useless_field(entry)
            formatted_bibtex.add(entry)
            print('update from dblp failed: ', title)
    return formatted_bibtex


def main():
    f = open("1.bib", "r")
    bibtex_str = f.read()
    a = bibtexparser.write_string(beautify(bibtex_str))
    f = open("2.bib", "w")
    f.write(a)


if __name__ == "__main__":
    main()
