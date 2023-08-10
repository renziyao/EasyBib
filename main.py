import requests
import os
import bibtexparser

keep_field = {
    'article': ['title', 'author', 'journal', 'year', 'volume', 'number', 'pages'],
    'inproceedings': ['title', 'author', 'booktitle', 'year', 'pages'],
}

venue_field = {
    'article': 'journal',
    'inproceedings': 'booktitle',
}

def beautify_bibtex(item):
    item_bib_str = requests.get(item["info"]["url"] + ".bib?param=1", verify=False).text
    item_bib = bibtexparser.parse_string(item_bib_str).entries[0]
    item_bib.fields = [field for field in item_bib.fields if field.key in keep_field[item_bib.entry_type]]
    if item["info"]["type"] in ["Journal Articles", "Conference and Workshop Papers"]:
        kw = {"q": "/".join(item["info"]["key"].split("/")[:2]), "format": "json"}
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


def beautify(bibtex_str):
    library = bibtexparser.parse_string(bibtex_str)
    print(f"Parsed {len(library.blocks)} blocks, including:"
          f"\n\t{len(library.entries)} entries"
          f"\n\t{len(library.comments)} comments"
          f"\n\t{len(library.strings)} strings and"
          f"\n\t{len(library.preambles)} preambles")
    formatted_bibtex = bibtexparser.Library()
    for entry in library.entries:
        try:
            kw = {"q": entry["title"], "format": "json", "h": 1000}
            res = requests.get("https://dblp.org/search/publ/api", verify=False, params=kw).json()
            for item in res['result']['hits']['hit']:
                # check title
                title_len = len(entry["title"].split(" "))
                score = float(item['@score'])
                if score < 0.8 * title_len:
                    continue
                # check author
                ...
                if score > 0.8 * title_len:
                    formatted_bibtex.add(beautify_bibtex(item))
                    break
        except:
            ...
    return formatted_bibtex


def main():
    bibtex_str = """
@article{DBLP:journals/tist/YangLCT19,
  author       = {Qiang Yang and
                  Yang Liu and
                  Tianjian Chen and
                  Yongxin Tong},
  title        = {Federated Machine Learning: Concept and Applications},
  journal      = {{ACM} Transactions on Intelligent Systems and Technology},
  volume       = {10},
  number       = {2},
  pages        = {12:1--12:19},
  year         = {2019},
}
    """
    a = bibtexparser.write_string(beautify(bibtex_str))
    print(a)


if __name__ == "__main__":
    main()
