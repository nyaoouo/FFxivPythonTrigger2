from FFxivPythonTrigger.memory import *
from .struct import Inventory
from . import AddressManager

####
# page types:
# 0-3：Backpack
# 1000：Equipment
# 2000: Currency
# 2001: Crystal
# 3500: Main hand
# 3200: Off hand
# 3201: Head
# 3202: Body
# 3203: Gloves
# 3204: Belt
# 3205: Leggings
# 3206: Feets
# 3207: Earring
# 3208: Necklace
# 3209: Bracelet
# 3300: Ring
# 3400: Soul Crystal
# 4000-4001: Chocobo backpack
# ---Current employee---
# 10000-10005: Backpack
# 11000: Equipment
# 12000: Currency
# 12001: Crystal
# 12002: Selling
####

_inventory = read_memory(POINTER(Inventory.InventoryPageIdx), AddressManager.inventory_ptr)

PAGE_TYPES = {
    "backpack": {0, 1, 2, 3},
    "equipment": {1000},
    "currency": {2000},
    "crystal": {2001},
    "mission_props": {2004},
    "main_hand": {3500},
    "off_hand": {3200},
    "head": {3201},
    "body": {3202},
    "gloves": {3203},
    "belt": {3204},
    "leggings": {3205},
    "feets": {3206},
    "earring": {3207},
    "necklace": {3208},
    "bracelet": {3209},
    "ring": {3300},
    "soul_crystal": {3400},
    "chocobo_backpack": {4000, 4001},
    "employee_backpack": {10000, 10001, 10002, 10003, 10004, 10005},
    "employee_equipment": {11000},
    "employee_currency": {12000},
    "employee_crystal": {12001},
    "employee_selling": {12002},
}


def get_inventory():
    if _inventory:
        return _inventory[0]


def get_item_in_pages(item_id, pages: set[int]):
    pages = pages.copy()
    inventory = get_inventory()
    if inventory is not None:
        for page in inventory:
            if page.type in pages:
                pages.remove(page.type)
                for item in page.get_items():
                    if item.id and (item_id is None or item.id == item_id):
                        yield item
                if not pages:
                    break


def get_pages_by_keys(*keys: str):
    ans = set()
    if keys == "*":
        for pages in PAGE_TYPES.values(): ans |= pages
    else:
        for key in keys: ans |= PAGE_TYPES[key]
    return ans


def get_item_in_pages_by_key(item_id, *keys: str):
    pages = get_pages_by_keys(*keys)
    return get_item_in_pages(item_id, pages)


export = type('obj', (object,), {
    'get_inventory': get_inventory,
    'get_item_in_pages': get_item_in_pages,
    'get_pages_by_keys': get_pages_by_keys,
    'get_item_in_pages_by_key': get_item_in_pages_by_key,
})
