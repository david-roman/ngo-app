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

#insert json
def load_redisjson(json_arr):

    r = Redis(port=6381)
    r.flushall()

    client = JClient(port=6381)

    for elem in json_arr:

        # Estimate members
        if elem['members'] is not None:

            if len(elem['members']) > 150:
                elem.pop('members', None)

            else: 
                numbers = re.findall(r'[0-9]+[.,]?[0-9]*', elem['members'])
                
                if len(numbers) > 0:
                    elem['members'] = sum(map(lambda num: int(num.replace(',', '').replace('.','')), numbers))
                    if elem['members'] == 0: elem.pop('members', None)
                
                else: 
                    elem.pop('members', None)

        # Filter established
        if elem['established'] == "0000":
            elem.pop('established', None)
        elif elem['established'] and elem['established'].isnumeric():
            elem['established'] = int(elem['established'])

        # Countries
        # TODO: Most countries inserted as None

        if elem['countries'] is not None and len(elem['countries']) > 0:
            if elem['countries'][0].lower() == 'none':
                elem.pop('countries', None)

            else:
                def setIsoName(country):
                    if "Ivoire" in country:
                        return "Ivory Coast"
                    elif "Palestine" in country:
                        return "Palestine, State of"
                    elif "Korea" in country:
                        return "South Korea"

                elem['countries'] = [setIsoName(country) for country in elem['countries']]

        # Text fields to one field
        text = ""

        if elem['statement'] is not None:
            text = elem['statement']

        remarks = elem['remarks']
        exclude = ['status', 'Status', 'application', 'Application', 'submit', 'suspend']
        if remarks is not None and (len(remarks) > 1000 or (len(remarks) > 200 \
            and not any(e in remarks for e in exclude))):
            
            text += " " + remarks
        
        elem['text'] = text

        #Delete old text fields
        elem.pop('statement', None)
        elem.pop('remarks', None)
    
        # JSON.SET name . 'elem'
        client.jsonset(elem['title'], Path.rootPath(), elem)

def main():

    with open("python/esango.json") as json_file:
    
        json_pre = json.load(json_file)

    print(len(json_pre))
    
    json_arr = list(filter(lambda item: has_info(item), json_pre))

    print(len(json_arr))

    load_redisjson(json_arr)

if __name__ == "__main__":
    main()