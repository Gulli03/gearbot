# dont rename this.. see blizzapi.py. Btw Bapi is a widespread SAP Api which is extra misleading ;)
import blizzapi as bapi

def getitemtrack(bonusid: list):
    # put docstring here
    trackstring = ""
    for id in bonusid:
        match id:
            # you can safe a lot of space and make this easier to read by using a dict which maps the id to the string
            # I'd also reccomend to get rid of rewriting Forscher/Abenteurer etc -> use variables..
            # Forscher
            case 10289:
                trackstring = "(Forscher 1/8)"
            case 10288:
                trackstring = "(Forscher 2/8)"
            case 10287:
                trackstring = "(Forscher 3/8)"
            case 10286:
                trackstring = "(Forscher 4/8)"
            case 10285:
                trackstring = "(Forscher 5/8)"
            case 10284:
                trackstring = "(Forscher 6/8)"
            case 10283:
                trackstring = "(Forscher 7/8)"
            case 10282:
                trackstring = "(Forscher 8/8)"

            # Abentuerer
            case 10297:
                trackstring = "(Abenteurer 1/8)"
            case 10296:
                trackstring = "(Abenteurer 2/8)"
            case 10295:
                trackstring = "(Abenteurer 3/8)"
            case 10294:
                trackstring = "(Abenteurer 4/8)"
            case 10293:
                trackstring = "(Abenteurer 5/8)"
            case 10292:
                trackstring = "(Abenteurer 6/8)"
            case 10291:
                trackstring = "(Abenteurer 7/8)"
            case 10290:
                trackstring = "(Abenteurer 8/8)"
            
            # Veteran
            case 10281:
                trackstring = "(Veteran 1/8)"
            case 10280:
                trackstring = "(Veteran 2/8)"
            case 10279:
                trackstring = "(Veteran 3/8)"
            case 10278:
                trackstring = "(Veteran 4/8)"
            case 10277:
                trackstring = "(Veteran 5/8)"
            case 10276:
                trackstring = "(Veteran 6/8)"
            case 10275:
                trackstring = "(Veteran 7/8)"
            case 10274:
                trackstring = "(Veteran 8/8)"

            # Champion
            case 10273:
                trackstring = "(Champion 1/8)"
            case 10272:
                trackstring = "(Champion 2/8)"
            case 10271:
                trackstring = "(Champion 3/8)"
            case 10270:
                trackstring = "(Champion 4/8)"
            case 10269:
                trackstring = "(Champion 5/8)"
            case 10268:
                trackstring = "(Champion 6/8)"
            case 10267:
                trackstring = "(Champion 7/8)"
            case 10266:
                trackstring = "(Champion 8/8)"
            
            # Held
            case 10265:
                trackstring = "(Held 1/6)"
            case 10264:
                trackstring = "(Held 2/6)"
            case 10263:
                trackstring = "(Held 3/6)"
            case 10262:
                trackstring = "(Held 4/6)"
            case 10261:
                trackstring = "(Held 5/6)"
            case 10256:
                trackstring = "(Held 6/6)"

            # Mythos
            case 10260:
                trackstring = "(Mythos 1/6)"
            case 10259:
                trackstring = "(Mythos 2/6)"
            case 10258:
                trackstring = "(Mythos 3/6)"
            case 10257:
                trackstring = "(Mythos 4/6)"
            case 10298:
                trackstring = "(Mythos 5/6)"
            case 10299:
                trackstring = "(Mythos 6/6)"

            # Crafted
            case 10222:
                trackstring = "(Crafted)"

    
    return trackstring

def getcharequip(name: str, realm: str):
    # dont use "raw", "name" as variable name (keyword in some languages)
    raw = bapi.characterequip(name, realm)
    # better do a try int() except here and catch the error
    # thats the more pythonic way to do it as type itself can raise an error
    if type(raw) == int:
        return raw

    # you should always change the variable name if you change the content
    raw = raw["equipped_items"]
    # you couold simplify this like this:  equip  = {"name": name, ... }
    equip = {}
    equip["name"] = name
    equip["realm"] = realm
    equip["embellishments"] = 0

    ilvl = 0
    # the following loop should get it's own function
    equip["gear"] = []
    for item in raw:
        # you may want to extend this later, so put ["Hemd", "Wappenrock"] in a variable caclled exclude_items at your function start

        if item["slot"]["name"] in ["Hemd", "Wappenrock"]:
            continue
        # extending a list in a dict with a dict is a bit too cryptic..
        # at least but the dict in a variable first, give it a good name and then append to your dict
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

        if "bonus_list" in item:
            yequip["gear"][-1]["itemtrack"] = getitemtrack(item["bonus_list"])
        else:
            # you better initalizes this at the beginning of the function
            equip["gear"][-1]["itemtrack"] = ""

        ilvl += item["level"]["value"]
        # Your functions should end here -> put all the bonus special stuff to another function
        
        #
        #       Sockel
        #
        #
        # for the following part you could put equip["gear"][-1] into a variable and just update that
        # your should put the "["Hals", "Ring 1", "Ring 2"]" special case to a variable so you dont have to repeat hthat
        if "sockets" in item:
            # you better initalizes this at the beginning of the function (you can remove the elif part then)
            equip["gear"][-1]["hassocket"] = True
            equip["gear"][-1]["sockets"] = []
            for sockel in item["sockets"]:
                equip["gear"][-1]["sockets"].append({"missing": False})
                equip["gear"][-1]["sockets"][-1]["hasgem"] = "item" in sockel

                if "item" in sockel:
                    equip["gear"][-1]["sockets"][-1]["item"] = sockel["item"]["name"]
                    equip["gear"][-1]["sockets"][-1]["description"] = sockel["display_string"]

            if (item["slot"]["name"] in ["Hals", "Ring 1", "Ring 2"]) and len(item["sockets"]) < 2:
                equip["gear"][-1]["sockets"].append({"missing": True})

        elif item["slot"]["name"] in ["Hals", "Ring 1", "Ring 2"]:
            equip["gear"][-1]["hassocket"] = True
            equip["gear"][-1]["sockets"] = []
            equip["gear"][-1]["sockets"].append({"missing": True})
            equip["gear"][-1]["sockets"].append({"missing": True})
        
        #
        #       Verzauberungen
        #
        #
        # Your functions should end here again -> put all the bonus special stuff to another function
        # despite that all from above applies to entchantments -> reducie dict call complexity by using variables for repeated dict calls
        # In general you should avoid extremely indented code.. 2-3 levels are readable, but anything above should be outsourced to another function
        
        if item["slot"]["name"] in ["Waffenhand", "Schildhand", "Rücken", "Handgelenk", "Füße", "Ring 1", "Ring 2", "Brust", "Beine"]:
            equip["gear"][-1]["hasenchantment"] = True
            equip["gear"][-1]["enchantment"] = [{}]
            istverzaubert = False
            if "enchantments" in item:
                for vz in item["enchantments"]:
                    if vz["enchantment_slot"]["type"] == "PERMANENT":
                        istverzaubert = True
                        equip["gear"][-1]["enchantment"][0]["missing"] = False

                        if "source_item" in vz:
                             equip["gear"][-1]["enchantment"][0]["item"] = vz["source_item"]["name"]
                        
                        if vz["display_string"].split("|")[0].split(":")[-1][1:-1][0] == "+":
                            equip["gear"][-1]["enchantment"][0]["description"] = " ".join(vz["display_string"].split("|")[0].split(":")[-1][1:-1].split(" ")[1:])
                        else:
                            equip["gear"][-1]["enchantment"][0]["description"] = vz["display_string"].split("|")[0].split(":")[-1][1:-1]

                        if len(vz["display_string"].split("|")) >= 1:
                            equip["gear"][-1]["enchantment"][0]["tier"] = vz["display_string"].split("|")[1].split(":")[1].split("-")[3]

            if not istverzaubert:
                if item["slot"]["name"] == "Schildhand" and not equip["gear"][-1]["type"] in ["WEAPON", "TWOHWEAPON"]:
                    equip["gear"][-1]["enchantment"][0]["missing"] = False
                else:
                    equip["gear"][-1]["enchantment"][0]["missing"] = True
    
        #
        #          Verzierungen
        #
        #
        if "limit_category" in item:
            if "Verziert" in item["limit_category"]:
                equip["gear"][-1]["hasembellishment"] = True
                equip["embellishments"] += 1

    equip["hasshield"] = any(item.get("slot") == "Schildhand" for item in equip["gear"])

    if not equip["hasshield"]:
        ilvl += equip["gear"][-1]["ilvl"]
    # describe what you do here.. better use a variable for the 16 ;)
    ilvl = round(ilvl / 16, 2)
    equip["avgilvl"] = ilvl

    return equip

def getcharclass(name: str, realm: str):
    raw = bapi.getcharspec(name, realm)
    if type(raw) == int:
        return raw
    # this is hardly to understand, try to use more varable assingments between directly assign this
    charclass = raw["specializations"][0]["loadouts"][0]["selected_class_talent_tree"]["name"]

    return charclass

def getcharmedia(name: str, realm: str):
    raw = bapi.getcharmedia(name, realm)
    if type(raw) == int:
        return raw
    
    media = {
        "portrait": raw["assets"][0]["value"],
        "panorama": raw["assets"][1]["value"],
        "raw": raw["assets"][2]["value"]
    }

    return media

def getitemmedia(itemid: int):
    raw = bapi.getitemmedia(itemid)
    if type(raw) == int:
        return raw
    
    icondata = [raw["assets"][0]["value"], raw["assets"][0]["file_data_id"]]
    return icondata

def classarmortype(charclass: str):
    match charclass:
        # same as in the first function in this file: better use a dcit mapping to make it more readable
        #   Stoff
        case "Priester":
            return "Stoff"
        case "Magier":
            return "Stoff"
        case "Hexenmeister":
            return "Stoff"
        
        #   Leder
        case "Schurke":
            return "Leder"
        case "Druide":
            return "Leder"
        case "Mönch":
            return "Leder"
        case "Dämonenjäger":
            return "Leder"
        
        # Kette
        case "Jäger":
            return "Kette"
        case "Schamane":
            return "Kette"
        case "Rufer":
            return "Kette"
        
        # Platte
        case "Krieger":
            return "Platte"
        case "Paladin":
            return "Platte"
        case "Todesritter":
            return "Platte"
        # you should describe this special case
        case _:
            print(charclass)
            return ""
