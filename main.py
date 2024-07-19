import json
import os
import requests


WORLD = 'Shiva' # id: 67

XIVAPI_URL = 'https://xivapi.com/'
UNIVERSALIS_URL = 'https://universalis.app/api/v2/'

# requests per sec
XIVAPI_RATE_LIMIT = 20
UNIVERSALIS_RATE_LIMIT = 25  


def get_cache_folder(cache_type):
    if cache_type == 'recipe':
        return 'cache/recipes/'
    if cache_type == 'icon':
        return 'cache/icons/'


def cache(cache_type=None, data=None):
    try:
        os.mkdir('cache')
        os.mkdir('cache/recipes')
        os.mkdir('cache/icons')
    except FileExistsError:
        pass
        
    # early return: no action needed
    if cache_type is None:
        return
    folder = get_cache_folder(cache_type)

    # early return: file already cached
    if os.path.isfile(f"{folder}{data['id']}.json"):
        return
    with open(f"{folder}{data['id']}.json", 'w', encoding='UTF-8') as f:
        f.write(json.dumps(data))
        

def is_cached(obj_id, cache_type):
    folder = 'cache/recipes/'
    return os.path.isfile(f"{folder}{obj_id}.json")
    

def get_cache(obj_id, cache_type):
    folder = get_cache_folder(cache_type)
    with open(f'{folder}{obj_id}.json', 'r', encoding='UTF-8') as f:
        return json.loads(f.read())
    

def get_json_from_api(url):
    res = requests.get(url, verify=False)  # ssl? stupid corporate proxy/firewall
    return json.loads(res.text)
    

def item_name_to_id(name):
    url = f"{XIVAPI_URL}search?string={name}"
    search = get_json_from_api(url)
        
    id_ = None
    for result in search['Results']:
        if result['UrlType'] == 'Recipe':
            id_ = result['ID']
            break
    return id_
    

def get_recipe_json(recipe_id):
    url = f"{XIVAPI_URL}Recipe/{recipe_id}"
    return get_json_from_api(url)
    
    
def get_recipe_tree(recipe_id):
    if is_cached(recipe_id, cache_type='recipe'):
        return get_cache(recipe_id)
    else:
        json_obj = get_recipe_json(recipe_id)  ## TODO fetch from api by item ID or maybe serach by name -> get id -> fetch
        item = {}
        item['name'] = json_obj['ItemResult']['Name']
        item['id'] = json_obj['ItemResult']['ID']
        item["icon"] = json_obj['Icon'],
        item['ingredients'] = []
        node = json_obj
        # print(item['name'])
        for i in range(8):
            if node['AmountIngredient' + str(i)] != 0:
                item['ingredients'].append({
                    "index": i,
                    "id": node['ItemIngredient' + str(i)]['ID'],
                    "name": node['ItemIngredient' + str(i)]['Name'],
                    "amount": node['AmountIngredient' + str(i)],
                    "icon": node['ItemIngredient' + str(i)]['Icon'],
                    "ingredients": []
                })
        
        for idx, ingredient in enumerate(item['ingredients']):
            index = idx
            # print(" -", ingredient['name'], "x" + str(ingredient['amount']))
            subnodes = node['ItemIngredientRecipe' + str(index)]
            if subnodes is None:
                continue
            subnode = subnodes[0]  # if there are multiple jobs who can create the item, this has a multiple elements
            for i in range(8):
                if subnode['AmountIngredient' + str(i)] != 0:
                    # print("   -", subnode['ItemIngredient' + str(i)]['Name'], "x" + str(subnode['AmountIngredient' + str(i)]))
                    item['ingredients'][index]['ingredients'].append({
                        "index": i,
                        "id": subnode['ItemIngredient' + str(i)]['ID'],
                        "name": subnode['ItemIngredient' + str(i)]['Name'],
                        "amount": subnode['AmountIngredient' + str(i)],
                        "icon": subnode['ItemIngredient' + str(i)]['Icon']
                    })
                    item['ingredients'][index]["amount_result"] = subnode['AmountResult'][0],
        # print('\n')
        cache(cache_type='recipe', data=item)

    return item
    
    
def get_prices(item):
    # https://universalis.app/api/v2/Shiva/43996?listings=5&entries=0
    # |--------- base url ---------|-world|-ids*-|         ^         ^
    #                           how many listings per item?      history size
    # * can be a single id or a comma-separated list of ids
    item_ids = [item['id']]
    for itm in item['ingredients']:
        item_ids.append(itm['id'])
        for itm_2 in itm['ingredients']:
            item_ids.append(itm_2['id'])

    item_ids = list(set(item_ids))
    # print(item_ids)

    url = f"{UNIVERSALIS_URL}{WORLD}/{','.join(str(itm) for itm in item_ids)}"
    url += "?listings=10&entries=0"
    # print(url)
    while True:
        res = requests.get(url, verify=False)
        
        # universalis api is overloaded, may take some attempts
        if res.status_code != 504:
            prices = json.loads(res.text)
            break
    
    sum_itm = 0
    for itm in item['ingredients']:
        id_ = itm['id']
        
        # make sure there are enough listings to craft at least one item for given price
        # this may result in a higher price though
        quantity = 0
        listing_n = 0
        while quantity < itm['amount']:
            quantity += prices['items'][str(id_)]['listings'][listing_n]['quantity']
            listing_n += 1
        itm['price'] = prices['items'][str(id_)]['listings'][listing_n]['pricePerUnit'] # without tax
        sum_itm_2 = 0
        for itm_2 in itm['ingredients']:
            id_ = itm_2['id']
            quantity = 0
            listing_n = 0
            while quantity < itm_2['amount']:
                quantity += prices['items'][str(id_)]['listings'][listing_n]['quantity']
                listing_n += 1
            itm_2['price'] = prices['items'][str(id_)]['listings'][listing_n]['pricePerUnit'] # without tax
            print(itm_2['name'], 'costs', itm_2['price'], 'x' + str(itm_2['amount']))
            sum_itm_2 += itm_2['price']*itm_2['amount']
        if len(itm['ingredients']) != 0:
            itm['price_if_crafted'] = sum_itm_2
        
        sum_itm += itm['price']*itm['amount'] 
    
    return item
    

def main(item_name):
    cache()
    recipe_id = item_name_to_id(item_name)
    item = get_recipe_tree(recipe_id)
    item = get_prices(item)
    print(json.dumps(item))
    

#main("Book of Ra'Kaznar")
main("Acqua Pazza")

# 42459 = Book of Ra'Kaznar (item) vs 
# 5985  = Recipe
# TODO
# - fetch icons online
# - cache icons
# - UI
# - fix calculation for multicraft (e.g. Sanctified Water which makes 3 and therefore makes it cheaper to craft (*1/3)