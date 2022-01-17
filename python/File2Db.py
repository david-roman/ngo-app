import json
from redis import Redis
from rejson import Client, Path
import re
import pycountry_convert as pc
import Preprocess

# Return true only if item has necessary info
def has_info(item):

    if not item['title'] or (not item['remarks'] and not item['statement']) or not item['activities']:
        return False;

    else:
        return True;

#insert json
def load_redisjson(json_arr):

    r = Redis(port=6381)
    # r.flushall()

    client = Client(port=6381, decode_responses=True)

    for elem in json_arr:

        if elem['acronym'] is not None and elem['acronym'] == 'ZAP':
            elem.pop('acronym', None)

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
        else:
            elem.pop('established', None)

        if elem['countries'] is not None and len(elem['countries']) > 0:
            if elem['countries'][0].lower() == 'none':
                elem.pop('countries', None)

            else:
            
                if "Holy See" in elem['countries']:
                    elem['countries'].remove("Holy See")
                if "Country Not Available" in elem['countries']:
                    elem['countries'].remove("Country Not Available")
                if "Timor-Leste" in elem['countries']:
                    elem['countries'].remove("Timor-Leste")
                if "-" in elem['countries']:
                    elem['countries'].remove("-")

                def setIsoName(country):
                    problematic = ["Palestine", "Venezuela", "Iran", "Bolivia", "Micronesia"]

                    if "Ivoire" in country:
                        return "Ivory Coast"
                    if "Bissau" in country:
                        return "Guinea-Bissau"
                    if "Republic of Korea" in country:
                        return "South Korea"
                    for word in country.split():
                        if word in problematic:
                            return word
                    
                    return country

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

        # activities
        activities = []
        for area in elem['activities']:
            activities = activities + elem['activities'][area]
        # Remove duplicates
        elem['activities'] = list(set(activities))

        # Set continents
                # Get ngo continents
        continents = {
            'NA': 'North America',
            'SA': 'South America', 
            'AS': 'Asia',
            'OC': 'Australia',
            'AF': 'Africa',
            'EU': 'Europe'
        }

        if elem['countries'] is not None:
            continentSet = set()
            for country in elem['countries']:
                if country is not None:
                    continentSet.add(continents[pc.country_alpha2_to_continent_code(pc.country_name_to_country_alpha2(country))])

            elem['continents'] = list(continentSet)
        else:
            elem['continents'] = []

    
        # JSON.SET name . 'elem'
        client.jsonset(elem['title'], Path.rootPath(), elem)

def main():

    with open("python/esango.json") as json_file:
    
        json_pre = json.load(json_file)

    print(len(json_pre))
    
    json_arr = list(filter(lambda item: has_info(item), json_pre))

    print(len(json_arr))

    load_redisjson(json_arr)

    print('Insertion completed')

    # Preprocess.numeric_preprocess()
    # print('Numeric preprocess completed')

    Preprocess.text_preprocess()
    print('Text completed')
    
    Preprocess.most_important_values()
    print('Most important values calculated')
    
    # Preprocess.most_significant_vars()
    # print('Most significant variables calculated')

if __name__ == "__main__":
    main()