import scrapy
from urllib.parse import urlparse, unquote
from lxml.html import fromstring
import lxml.etree
import json
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO


def clean_text(text):
    out = []
    for line in text:
        for i in range(10):
            line = line.replace("\n\n", "\n")
            line = line.replace("\r\n", "\n")
            line = line.replace("\n\r", "\n")
            line = line.replace("\r", "\n")
        if len(line) != 0:
            out.append(line)

    out2 = []
    tables = []
    current = ""
    for line in out:
        last = current
        current = line
        if last != current and last == "\n":
            pass
        else:
            # Check if line is a table
            if "<table" in line and "</table>" in line:
                # Convert to CSV
                try:
                    tables.extend(convert_html_table_to_csv([line]))
                except Exception as e:
                    raise (e)
            else:
                out2.append(line)

    if any(tables):
        out2.extend(tables)

    return out2


class generic_scrapper(scrapy.Spider):
    start_urls = ["https://machineguard.com/",
                  "https://machineguard.com/machine-guarding/",
                  "https://machineguard.com/machine-guarding/standard-guards/standard-flanged-guards/"]
    name = 'generic'

    simple_context_tree = {}

    simple_context_tree["root"] = {"xpath": "/html/body/text()[not(parent::script or parent::style or parent::table)]"}
    simple_context_tree["root"]["children"] = {}
    simple_context_tree["root"]["children"]["section"] = {
        "xpath": "/html/body/div[1]/div/div[3]/div/section[not(.//table)]"}
    simple_context_tree["root"]["children"]["section"]["children"] = {}
    simple_context_tree["root"]["children"]["section"]["children"]["section"] = {
        "xpath": "/html/body/div[1]/div/div[3]/div/section/article/section/table"}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        parsed_url = urlparse(response.url)
        filename = unquote(parsed_url.path.strip('/').split('/')[-1]) or parsed_url.netloc
        filename += ".txt"
        print(f"filename: {filename}")

        clean_text = self.parse_xpath(response, self.simple_context_tree)

        # Clean the text
        if isinstance(clean_text, str):
            clean_text = [clean_text]

        out = []
        for i, text_seg in enumerate(clean_text):
            if isinstance(text_seg, list):
                out.append([text.strip() for text in text_seg if text.strip() != ""])
                if out[-1]==[]:
                    out.pop(-1)
            else:
                out.append(text_seg.strip())
                if out[-1]=="":
                    out.pop(-1)

            # Write text to file
        with open(filename, 'w', encoding='utf-8') as f:
            for text in out:
                # Convert list to JSON and write to file
                json.dump(text, f)
                f.write('\n')  # Write a newline character after each JSON object

    def parse_xpath(self, response, tree):
        texts = []
        for key, value in tree.items():
            if key == "xpath":
                print(f"xpath: {value}")
                data = response.xpath(value).getall()
                # Strip attributes from HTML tags
                for i, html in enumerate(data):
                    try:
                        tree = fromstring(html)
                        for elem in tree.iter():
                            elem.attrib.clear()  # Remove attributes
                        data[i] = lxml.etree.tostring(tree, encoding='unicode')
                    except lxml.etree.ParserError:
                        pass
                data = clean_text(data)
                print(data)
                texts.extend(data)
            if key == "children":
                texts.extend(self.parse_xpath(response, value))
            if key == "section" or key == "root":
                texts.extend(self.parse_xpath(response, value))
        return texts


def convert_html_table_to_csv(html_data):
    if isinstance(html_data, str):
        html_data = [html_data]

    csv_list = []
    for i, html in enumerate(html_data):
        soup = BeautifulSoup(html, 'lxml')  # Parse the HTML as a string

        # Find all tables on the page
        tables = soup.find_all('table')

        csv_data = []

        for i, table in enumerate(tables):
            # Create a DataFrame from the table
            df = pd.read_html(str(table), header=0)[0]

            # Convert DataFrame to CSV string
            csv_str = StringIO()
            df.to_csv(csv_str, index=False)
            csv_data.append(csv_str.getvalue())

        csv_list.append(csv_data)

    return csv_list
