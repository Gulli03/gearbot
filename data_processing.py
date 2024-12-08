"""
dataprocessing
~~~~~~~~~~~~

This module implements the processing of data gotten from the Blizzard-Api.

"""

import blizzapi


def get_bonus_string(bonus_id_list: list) -> str:
    """
    Checks every bonus-ID of an Item and stores Information about the Upgrade-track inside a string
    :param bonus_id_list: A list of the bonus-ID's an item has
    :return: A string containing Information about the Upgrade-track of an item
    """
    bonus_string = ""
    tracknames = ["Forscher", "Abenteurer", "Veteran", "Champion", "Held", "Mythos"]
    bonus_id_dict = {
        # Forscher
        "10289": f"({tracknames[0]} 1/8)",
        "10288": f"({tracknames[0]} 2/8)",
        "10287": f"({tracknames[0]} 3/8)",
        "10286": f"({tracknames[0]} 4/8)",
        "10285": f"({tracknames[0]} 5/8)",
        "10284": f"({tracknames[0]} 6/8)",
        "10283": f"({tracknames[0]} 7/8)",
        "10282": f"({tracknames[0]} 9/8)",

        # Abenteuerer
        "10297": f"({tracknames[1]} 1/8)",
        "10296": f"({tracknames[1]} 2/8)",
        "10295": f"({tracknames[1]} 3/8)",
        "10294": f"({tracknames[1]} 4/8)",
        "10293": f"({tracknames[1]} 5/8)",
        "10292": f"({tracknames[1]} 6/8)",
        "10291": f"({tracknames[1]} 7/8)",
        "10290": f"({tracknames[1]} 9/8)",

        # Veteran
        "10281": f"({tracknames[2]} 1/8)",
        "10280": f"({tracknames[2]} 2/8)",
        "10279": f"({tracknames[2]} 3/8)",
        "10278": f"({tracknames[2]} 4/8)",
        "10277": f"({tracknames[2]} 5/8)",
        "10276": f"({tracknames[2]} 6/8)",
        "10275": f"({tracknames[2]} 7/8)",
        "10274": f"({tracknames[2]} 9/8)",

        # Champion
        "10273": f"({tracknames[3]} 1/8)",
        "10272": f"({tracknames[3]} 2/8)",
        "10271": f"({tracknames[3]} 3/8)",
        "10270": f"({tracknames[3]} 4/8)",
        "10269": f"({tracknames[3]} 5/8)",
        "10268": f"({tracknames[3]} 6/8)",
        "10267": f"({tracknames[3]} 7/8)",
        "10266": f"({tracknames[3]} 9/8)",

        # Held
        "10265": f"({tracknames[4]} 1/6)",
        "10264": f"({tracknames[4]} 2/6)",
        "10263": f"({tracknames[4]} 3/6)",
        "10262": f"({tracknames[4]} 4/6)",
        "10261": f"({tracknames[4]} 5/6)",
        "10256": f"({tracknames[4]} 6/6)",

        # Mythos
        "10260": f"({tracknames[5]} 1/6)",
        "10259": f"({tracknames[5]} 2/6)",
        "10258": f"({tracknames[5]} 3/6)",
        "10257": f"({tracknames[5]} 4/6)",
        "10298": f"({tracknames[5]} 5/6)",
        "10299": f"({tracknames[5]} 6/6)",

        # Crafted
        "10222": "(Crafted)"
    }

    for bonus_id in bonus_id_list:
        if str(bonus_id) in bonus_id_dict:
            bonus_string = bonus_id_dict[str(bonus_id)]

    return bonus_string


def get_char_equip(name: str, realm: str):
    """
    Gets the equipment of the given Character form the blizzard-api and converts it into a much more usable format
    :param name: Name of the Character
    :param realm: Name of the Realm of the Character
    :return: Either a dictionary of the Character Equipment, or the status code of the response
    """
    character_equip_response = blizzapi.get_character_info(name, realm, "equipment")
    try:
        int(character_equip_response)
        return character_equip_response
    except TypeError:
        pass
    character_equip_raw = character_equip_response["equipped_items"]
    character = {"name": name, "realm": realm, "equip": process_equipment(character_equip_raw)}
    return character


def process_equipment(character_equip_raw: list) -> dict:
    """
    Goes through each item in the unprocessed list and makes a new, cleaner list with only the important information
    :param character_equip_raw: The unprocessed equipment list from the api
    :return: A cleaned up version of this equipmet list with additional helpful info
    """
    ilvl = 0
    equip = {"gear": [], "embellishments": 0}
    for item in character_equip_raw:
        if item["slot"]["name"] in ["Hemd", "Wappenrock"]:
            continue

        equip["gear"].append({
            "slot": item["slot"]["name"],
            "name": item["name"],
            "id": item["item"]["id"],
            "ilvl": item["level"]["value"],
            "hassocket": False,
            "hasenchantment": False,
            "hasembellishment": False,
            "type": item["inventory_type"]["type"]
        })

        current_item = equip["gear"][-1]

        ilvl += item["level"]["value"]

        if "bonus_list" in item:
            current_item["itemtrack"] = get_bonus_string(item["bonus_list"])
        else:
            current_item["itemtrack"] = ""

        get_sockets(current_item, item)

        get_enchantment(current_item, item)

        get_embellishment(current_item, item)

        if current_item["hasembellishment"]:
            equip["embellishments"] += 1

        equip["gear"][-1] = current_item

    equip["hasshield"] = any(item.get("slot") == "Schildhand" for item in equip["gear"])
    if not equip["hasshield"]:
        ilvl += current_item["ilvl"]
    number_of_slots = 16
    ilvl = round(ilvl / number_of_slots, 2)
    equip["avgilvl"] = ilvl

    return equip


def get_embellishment(current_item: dict, item: dict):
    """
    Checks if the item has an embellishent
    :param current_item: The dictionary in which to store the information
    :param item: The item that is checked
    """
    if "limit_category" in item:
        if "Verziert" in item["limit_category"]:
            current_item["hasembellishment"] = True


def get_enchantment(current_item: dict, item: dict):
    """
    Checks if the item is enchanted
    :param current_item: The dictionary in which to store the information
    :param item: The item that is checked
    """
    if item["slot"]["name"] in ["Waffenhand", "Schildhand", "Rücken", "Handgelenk", "Füße", "Ring 1", "Ring 2",
                                "Brust", "Beine"]:
        current_item["hasenchantment"] = True
        current_item["enchantment"] = [{}]
        istverzaubert = False
        if "enchantments" in item:
            for vz in item["enchantments"]:
                if vz["enchantment_slot"]["type"] == "PERMANENT":
                    istverzaubert = True
                    current_item["enchantment"][0]["missing"] = False

                    if "source_item" in vz:
                        current_item["enchantment"][0]["item"] = vz["source_item"]["name"]

                    if vz["display_string"].split("|")[0].split(":")[-1][1:-1][0] == "+":
                        current_item["enchantment"][0]["description"] = " ".join(
                            vz["display_string"].split("|")[0].split(":")[-1][1:-1].split(" ")[1:])
                    else:
                        current_item["enchantment"][0]["description"] = \
                            vz["display_string"].split("|")[0].split(":")[-1][1:-1]

                    if len(vz["display_string"].split("|")) >= 1:
                        current_item["enchantment"][0]["tier"] = \
                            vz["display_string"].split("|")[1].split(":")[1].split("-")[3]

        if not istverzaubert:
            if item["slot"]["name"] == "Schildhand" and not current_item["type"] in ["WEAPON", "TWOHWEAPON"]:
                current_item["enchantment"][0]["missing"] = False
            else:
                current_item["enchantment"][0]["missing"] = True


def get_sockets(current_item: dict, item: dict):
    """
    Checks if the item has sockets
    :param current_item: The dictionary in which to store the information
    :param item: The item that is checked
    """
    if "sockets" in item:
        current_item["hassocket"] = True
        current_item["sockets"] = []
        for sockel in item["sockets"]:
            current_item["sockets"].append({"missing": False})
            current_item["sockets"][-1]["hasgem"] = "item" in sockel

            if "item" in sockel:
                current_item["sockets"][-1]["item"] = sockel["item"]["name"]
                current_item["sockets"][-1]["description"] = sockel["display_string"]

        if (item["slot"]["name"] in ["Hals", "Ring 1", "Ring 2"]) and len(item["sockets"]) < 2:
            current_item["sockets"].append({"missing": True})

    elif item["slot"]["name"] in ["Hals", "Ring 1", "Ring 2"]:
        current_item["hassocket"] = True
        current_item["sockets"] = []
        current_item["sockets"].append({"missing": True})
        current_item["sockets"].append({"missing": True})


def get_char_class(name: str, realm: str):
    """
    Gets the class of the given Character from the blizzard-api
    :param name: Name of the Character
    :param realm: Name of the Realm of the Character
    :return: Name of the Class of the Character, or the status code of the response
    """
    character_spec_response = blizzapi.get_character_info(name, realm, "specializations")
    try:
        int(character_spec_response)
        return character_spec_response
    except TypeError:
        pass

    charclass = character_spec_response["specializations"][0]["loadouts"][0]["selected_class_talent_tree"]["name"]

    return charclass


def get_char_media(name: str, realm: str):
    """
    Gets the media of the given Character from the blizzard-api
    :param name:Name of the Character
    :param realm:Name of the Realm of the Character
    :return:A list with urls for a portrait, a panorama, and a raw picture of the character,
    or the status code of the response
    """
    character_media_response = blizzapi.get_character_info(name, realm, "character-media")
    try:
        int(character_media_response)
        return character_media_response
    except TypeError:
        pass

    media = {
        "portrait": character_media_response["assets"][0]["value"],
        "panorama": character_media_response["assets"][1]["value"],
        "raw": character_media_response["assets"][2]["value"]
    }

    return media


def get_item_media(itemid: int):
    """
    Get the media of the given Item-ID from the blizzard-api
    :param itemid: ID of the Item that is requested
    :return: A list with the url of the item-icon and the id of the icon, or the status code of the response
    """
    item_media_response = blizzapi.getitemmedia(itemid)
    try:
        int(item_media_response)
        return item_media_response
    except TypeError:
        pass

    icondata = [item_media_response["assets"][0]["value"], item_media_response["assets"][0]["file_data_id"]]
    return icondata


def class_armor_type(charclass: str) -> str:
    """
    Looks up the armor type for the given class
    :param charclass: The name of the class
    :return:The Armor-type that class wears, or empty string if class is not found
    """
    armor_type = {
        # Stoff
        "Priester": "Stoff",
        "Magier": "Stoff",
        "Hexenmeister": "Stoff",

        # Leder
        "Schurke": "Leder",
        "Druide": "Leder",
        "Mönch": "Leder",
        "Dämonenjäger": "Leder",

        # Kette
        "Jäger": "Kette",
        "Schamane": "Kette",
        "Rufer": "Kette",

        # Platte
        "Krieger": "Platte",
        "Paladin": "Platte",
        "Todesritter": "Platte"
    }
    if charclass in armor_type:
        return armor_type[charclass]
    else:
        print(charclass)
        return ""


if __name__ == "__main__":
    print(get_char_equip("estalia", "todeswache"))
