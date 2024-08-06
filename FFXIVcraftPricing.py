import json
import os
import time
import requests
from typing import Union


WORLD = 'Shiva'  # id: 67

XIVAPI_URL = 'https://xivapi.com/'
UNIVERSALIS_URL = 'https://universalis.app/api/v2/'

# requests per sec
XIVAPI_RATE_LIMIT = 20
UNIVERSALIS_RATE_LIMIT = 25  

CHECK_CERT = False   # deactivate if SSL errors occur


def get_cache_folder(cache_type: str) -> str:
    if cache_type == 'recipe':
        return 'cache/recipes/'
    if cache_type == 'icon':
        return 'cache/icons/'


def cache(cache_type: str = None, data: dict = None) -> None:
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
    if os.path.isfile(f"{folder}{data.get('id')}.json"):
        return
    with open(f"{folder}{data.get('id')}.json", 'w', encoding='UTF-8') as f:
        f.write(json.dumps(data))
        

def is_cached(obj_id: Union[int, str], cache_type: str) -> bool:
    folder = get_cache_folder(cache_type)
    ext = {'recipe': 'json', 'icon': 'png'}
    return os.path.isfile(f"{folder}{obj_id}.{ext.get(cache_type)}")
    

def get_cache(obj_id: int, cache_type: str) -> dict:
    folder = get_cache_folder(cache_type)
    with open(f'{folder}{obj_id}.json', 'r', encoding='UTF-8') as f:
        return json.loads(f.read())
    

def get_json_from_api(url: str) -> dict:
    res = requests.get(url, verify=CHECK_CERT)  # ssl? stupid corporate proxy/firewall
    return json.loads(res.text)
    

def item_name_to_id(name: str) -> int:
    url = f"{XIVAPI_URL}search?string={name}"
    search = get_json_from_api(url)
        
    id_ = None
    for result in search['Results']:
        if result.get('UrlType') == 'Recipe':
            id_ = result.get('ID')
            break
    return id_
    

def get_recipe_json(recipe_id: int) -> dict:
    url = f"{XIVAPI_URL}Recipe/{recipe_id}"
    return get_json_from_api(url)
    
    
def get_recipe_tree(recipe_id: int) -> dict:
    if is_cached(recipe_id, cache_type='recipe'):
        return get_cache(recipe_id, 'recipe')
    else:
        json_obj = get_recipe_json(recipe_id)
        item = {
            'name': json_obj.get('ItemResult').get('Name'),
            'id': json_obj.get('ItemResult').get('ID'),
            "icon": json_obj.get('Icon'),
            'ingredients': []
        }
        node = json_obj
        for i in range(8):
            if node['AmountIngredient' + str(i)] != 0:
                item['ingredients'].append({
                    "index": i,
                    "id": node.get('ItemIngredient' + str(i)).get('ID'),
                    "name": node.get('ItemIngredient' + str(i)).get('Name'),
                    "amount": node.get('AmountIngredient' + str(i)),
                    "icon": node.get('ItemIngredient' + str(i)).get('Icon'),
                    "ingredients": []
                })
        
        for idx, ingredient in enumerate(item.get('ingredients')):
            index = idx
            subnodes = node.get('ItemIngredientRecipe' + str(index))
            if subnodes is None:
                continue
            subnode = subnodes[0]  # if there are multiple jobs who can create the item, this has a multiple elements
            for i in range(8):
                if subnode.get('AmountIngredient' + str(i)) != 0:
                    item['ingredients'][index]['ingredients'].append({
                        "index": i,
                        "id": subnode.get('ItemIngredient' + str(i)).get('ID'),
                        "name": subnode.get('ItemIngredient' + str(i)).get('Name'),
                        "amount": subnode.get('AmountIngredient' + str(i)),
                        "icon": subnode.get('ItemIngredient' + str(i)).get('Icon')
                    })
                    item['ingredients'][index]["amount_result"] = subnode.get('AmountResult')
        cache(cache_type='recipe', data=item)

    return item
    
    
def get_prices(item: dict) -> dict:
    # https://universalis.app/api/v2/Shiva/43996?listings=5&entries=0
    # |--------- base url ---------|-world|-ids*-|        ^         ^
    #                           how many listings per item?      history size
    # * can be a single id or a comma-separated list of ids
    item_ids = [item.get('id')]
    for itm in item.get('ingredients'):
        item_ids.append(itm.get('id'))
        for itm_2 in itm.get('ingredients'):
            item_ids.append(itm_2.get('id'))

    item_ids = list(set(item_ids))

    url = f"{UNIVERSALIS_URL}{WORLD}/{','.join(str(itm) for itm in item_ids)}"
    url += "?listings=10&entries=0"
    
    print("Fetching prices...")
    while True:
        res = requests.get(url, verify=CHECK_CERT)
        
        # universalis api is overloaded most of the time, may take a few attempts
        if res.status_code == 504:
            print("Prices API overloaded. Retrying...")
        else:
            prices = json.loads(res.text)
            break
    
    sum_itm = 0
    for itm in item.get('ingredients'):
        id_ = itm.get('id')
        
        # make sure there are enough listings to craft at least one item for given price
        # this may result in a higher price though
        quantity = 0
        listing_n = 0
        while quantity < itm.get('amount') and listing_n >= len(prices.get('items').get(str(id_)).get('listings')):
            quantity += prices.get('items').get(str(id_)).get('listings')[listing_n].get('quantity')
            listing_n += 1
        itm['price'] = prices.get('items').get(str(id_)).get('listings')[listing_n].get('pricePerUnit')
        sum_itm_2 = 0
        for itm_2 in itm.get('ingredients'):
            id_ = itm_2['id']
            quantity = 0
            listing_n = 0
            while quantity < itm_2.get('amount'):
                quantity += prices.get('items').get(str(id_)).get('listings')[listing_n].get('quantity')
                listing_n += 1
            itm_2['price'] = prices.get('items').get(str(id_)).get('listings')[listing_n].get('pricePerUnit')
            sum_itm_2 += itm_2.get('price')*itm_2.get('amount')
        if len(itm.get('ingredients')) != 0:
            itm['price_if_crafted'] = int(sum_itm_2/itm.get('amount_result'))
        
        sum_itm += itm.get('price')*itm.get('amount')
    
    return item


def display_result(item):  # name subject to change
    txt = ''
    txt += f"{item.get('name'):24.23}{'#':>4}{'craft':>7}{'buy':>7}\n"
    for ingredient in item.get('ingredients'):
        txt += (f"  {ingredient.get('name'):22.21}{ingredient.get('amount'):>4}"
                f"{ingredient.get('price_if_crafted', ''):>7}{ingredient.get('price'):>7}\n")
        for sub_ingredient in ingredient.get('ingredients'):
            txt += (f"    {sub_ingredient.get('name'):20.19}{sub_ingredient.get('amount'):4}{'':>7}"
                    f"{sub_ingredient.get('price'):>7}\n")
    return txt
    

def generate_result(item_name):
    cache()
    recipe_id = item_name_to_id(item_name)
    if recipe_id is None:
        return None
    item = get_recipe_tree(recipe_id)
    item = get_prices(item)
    return item


def get_icon_list(recipe: dict) -> list[str]:
    icons = [recipe.get('icon')]
    for item in recipe.get('ingredients'):
        icons.append(item.get('icon'))
        for subitem in item.get('ingredients'):
            icons.append(subitem.get('icon'))
    return icons


def cache_icons(icon_urls: list[str]) -> None:
    # fetch icons from api and cache them
    # print(icon_urls)
    icon_urls = list(set(icon_urls))  # make sure every url is unique to reduce overhead
    for num, url in enumerate(icon_urls):
        icon_name = url.split('/')[-1]
        # don't fetch again if icon is already present
        if is_cached(icon_name.split('.')[0], 'icon'):
            continue
        res = requests.get(XIVAPI_URL + url, verify=CHECK_CERT, stream=True)
        if res.status_code == 200:
            base_path = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(base_path, 'cache', 'icons', icon_name), 'wb') as f:
                f.write(res.content)
        # respect the API's rate limit. Better way would be to time the actual request, but this way is quick and dirty.
        if num % XIVAPI_RATE_LIMIT == 0 and num > 0:
            time.sleep(1.)
