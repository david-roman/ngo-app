import json
from os import replace
from redis import Redis
from redisearch import Client as SClient
from redisearch.client import TextField
from rejson import Client as JClient, Path
import re

# Return true only if item has necessary info
def has_info(item):

    if not item['title'] or (not item['remarks'] and not item['statement']) or not item['activities']:

        return False;

    else:
        return True;

# Obtain and insert text fields from json
def load_redisearch(json_arr):

    r = Redis(port=6380)
    r.flushall()

    # FT.CREATE textIndex SCHEMA desc TEXT
    client = SClient("textIndex", port=6380)
    
    client.create_index([TextField('desc')])

    for elem in json_arr:

        text = ""

        if elem['statement'] is not None:
            text = elem['statement']

        remarks = elem['remarks']
        exclude = ['status', 'Status', 'application', 'Application', 'submit', 'suspend']
        if remarks is not None and (len(remarks) > 1000 or (len(remarks) > 200 and not any(e in remarks for e in exclude))):
            
            text += " " + remarks
    
        if text:

            # FT.ADD textIndex name 1.0 FIELDS desc "text"
            client.add_document(elem['title'], desc=text)

#insert json
def load_redisjson(json_arr):

    r = Redis(port=6381)
    r.flushall()

    client = JClient(port=6381)

    for elem in json_arr:

        #Delete textual fields
        elem.pop('statement', None)
        elem.pop('remarks', None)

        if elem['members'] is not None:

            if len(elem['members']) > 150:
                elem.pop('members', None)

            else: 
                numbers = re.findall(r'[0-9]+[.,]?[0-9]*', elem['members'])
                
                if len(numbers) > 0:
                    print
                    elem['members'] = sum(map(lambda num: int(num.replace(',', '').replace('.','')), numbers))
                    if elem['members'] == 0: elem.pop('members', None)
                
                else: 
                    elem.pop('members', None);

        # JSON.SET name . 'elem'
        client.jsonset(elem['title'], Path.rootPath(), elem)

def main():

    with open("python/esango.json") as json_file:
    
        json_pre = json.load(json_file)

    print(len(json_pre))
    
    json_arr = list(filter(lambda item: has_info(item), json_pre))

    print(len(json_arr))

    load_redisearch(json_arr)
    load_redisjson(json_arr)

if __name__ == "__main__":
    main()