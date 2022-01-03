"""
Modul dotáže databázi uzavřených provozoven na webu https://www.potravinynapranyri.cz
a výsledek uloží do csv souboru.

Inspirované následujícím příspěvkem:

David Beazley | Keynote: Built in Super Heroes
https://www.youtube.com/watch?v=lyDLAutA88s
"""

import csv
import datetime

import requests
import lxml.html


def get_id(id_string):
    start, end = id_string.find('id='), id_string.find('&')
    return id_string[start + 3 : end]


def process_offenses(raw_offenses):
    return '|'.join(offens.strip() for offens in raw_offenses)


def request_html(s, url, params, headers):
    r = s.get(url, params=params, headers=headers, timeout=3)
    html = lxml.html.fromstring(r.text)
    return html


def get_last_page_index(html):
    href_string = html.xpath('//a[@class="last"]/@href')[0]
    return int(href_string.split('&page=')[-1])


def get_data(s, html, headers):
    detail_url = 'https://www.potravinynapranyri.cz/WDetail.aspx'

    trs = html.xpath("//table/tr")[1:]  # skip table header

    data = []

    for tr in trs:
        facility = {}

        # Data from the table
        id_string = tr.xpath('@onclick')[0]
        facility['id'] = get_id(id_string)

        facility['druh'] = tr.xpath('td')[0].xpath('img/@title')[0]

        facility['nazev'] = tr.xpath('td')[1].xpath('span/text()')[0]
        facility['adresa'] = tr.xpath('td')[2].xpath('span/text()')[0]
        published = tr.xpath('td')[3].xpath('text()')[0]
        facility['datum_zverejneni'] = datetime.datetime.strptime(published, '%d. %m. %Y').date().isoformat()
        facility['zjistene_skutecnosti'] = process_offenses(tr.xpath('td')[4].xpath('span/text()'))

        # Data from the detail page
        detail_html = request_html(
            s,
            detail_url,
            params={'id': facility['id']},
            headers=headers,
        )
        try:
            ic = detail_html.xpath('//span[@id="MainContent_lblWsDetailIC"]/text()')[0]
        except IndexError:
            ic = None
        state = detail_html.xpath('//a[@id="MainContent_lnkWsDetailCloseState"]/text()')[0]
        closed = detail_html.xpath('//span[@id="MainContent_lblWsDetailCloseDate"]/text()')[0]
        try:
            opened = detail_html.xpath('//span[@id="MainContent_lblWsDetailReopenDate"]/text()')[0]
        except IndexError:
            opened = None
        ref_num = detail_html.xpath('//span[@id="MainContent_lblWsDetailReferenceNumber"]/text()')[0]

        facility['ico'] = ic
        facility['stav_uzavreni'] = state
        facility['datum_uzavreni'] = datetime.datetime.strptime(closed, '%d. %m. %Y').date().isoformat()
        try:
            facility['datum_uvolneni_zakazu'] = datetime.datetime.strptime(opened, '%d. %m. %Y').date().isoformat()
        except TypeError:
            facility['datum_uvolneni_zakazu'] = None
        facility['referencni_cislo'] = ref_num

        facility['stazeno'] = datetime.date.today().isoformat()

        data.append(facility)

    return data


def facilities_to_csv(
    start_url='https://www.potravinynapranyri.cz/WSearch.aspx',
    params={
        'lang': 'cs',
        'design': 'default',
        'archive': 'actual',
        'listtype': 'table',
        'page': '1',
    },
    output_filename='actual.csv',
):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=4)
    s.mount('https://', a)

    html = request_html(s, start_url, params, headers)  # first request only to get number of pages
    last_page_index = get_last_page_index(html)

    data = []

    for i in range(1, last_page_index + 1):
        params['page'] = i
        html = request_html(s, start_url, params, headers)
        new_data = get_data(s, html, headers=headers)
        data.extend(new_data)
        print(f'Parsed page {i} of {last_page_index} and added {len(new_data)} to list.')

    with open(output_filename, 'w') as file:
        fieldnames = [
            'id',
            'referencni_cislo',
            'ico',
            'nazev',
            'adresa',
            'datum_zverejneni',
            'datum_uzavreni',
            'datum_uvolneni_zakazu',
            'stav_uzavreni',
            'druh',
            'zjistene_skutecnosti',
            'stazeno',
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':
    facilities_to_csv()
    facilities_to_csv(
        params={
            'lang': 'cs',
            'design': 'default',
            'archive': 'archive',  # This is different
            'listtype': 'table',
            'page': '1',
        },
        output_filename='archive.csv',
    )
