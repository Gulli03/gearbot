"""
discordbot
~~~~~~~~~~~~

This module implements a discord bot for requesting Information about World of Warcraft Characters.

"""

import json
from typing import List, Any, Dict

import discord
import requests

import data_processing

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
last_raidcheck_result = []


#
#       Classes
#

class CharSelect(discord.ui.Select):
    def __init__(self, charlist: list):
        options = []
        for char in charlist:
            options.append(discord.SelectOption(label=char))
        super().__init__(placeholder="Wähle einen Charakter für mehr Details", max_values=1, min_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        global last_raidcheck_result
        await interaction.response.defer(ephemeral=True, thinking=True)
        playerlist = get_raidlist()
        charnamelist = get_charnames_from_raidlist(playerlist)
        character_index = charnamelist.index(self.values[0])
        selectedchar = playerlist[character_index]
        name = selectedchar["name"]
        realm = selectedchar["realm"]
        clean_name = name.lower()
        clean_realm = "-".join(realm.split(" ")).lower().replace("'", "")
        equip = last_raidcheck_result[character_index]
        equip["class"] = data_processing.get_char_class(clean_name, clean_realm)
        equip["thumbnail"] = data_processing.get_char_media(clean_name, clean_realm)["portrait"]
        gearembed = await construct_gearembed(name, realm, equip)
        await interaction.followup.send(embed=gearembed, ephemeral=True)


class SelectView(discord.ui.View):
    def __init__(self, *, timeout=1800, select):
        super().__init__(timeout=timeout)
        self.add_item(select)


#
#       Functions
#

def get_raidlist() -> list:
    """
    Reads the list of Characters in the Raidlist from file
    :return: A list containing every Characters Name, Realm and their connected Discord-ID that is in the raidlist
    """
    file = open("raidplayerlist.json", "r")
    playerlist = json.load(file)
    file.close()
    return playerlist


def get_charnames_from_raidlist(playerlist: list) -> list:
    """
    This takes a list containing dictionaries with name and realm keys for a character and converts them
    into a visually better format.
    :param playerlist: The List in the format [{"name": name, "realm": "realm}, {"name": name, "realm": "realm}]
    :return: A List with all Characternames of the input list, joined with the realmname
    """
    charnamelist = []
    for character in playerlist:
        charnamelist.append(character["name"] + "-" + character["realm"])
    return charnamelist


def save_raidlist(playerlist: list):
    """
    Saves the playerlist to a file
    :param playerlist: A List of players in the raid
    """
    file = open("raidplayerlist.json", "w")
    json.dump(playerlist, file, indent=4)
    file.close()


def save_settings(settingsdict: dict):
    """
    Saves the settings to a file
    :param settingsdict: A dictionary conataining the settings
    """
    file = open("settings.json", "w")
    json.dump(settingsdict, file, indent=4)
    file.close()


def load_settings() -> dict:
    """
    Reads the settings from a file
    :return: Dictionary conatining the settings
    """
    file = open("settings.json", "r")
    settingsdict = json.load(file)
    file.close()
    return settingsdict


def class_to_color(classname: str) -> int:
    """
    Looks up the color-code for a given class
    :param classname: The name of the class
    :return: The color-code in decimal for the class
    """
    colordict = {
        "Druide": 16743434,  # FF7C0A
        "Dämonenjäger": 10694857,  # A330C9
        "Hexenmeister": 8882414,  # 8788EE
        "Jäger": 11195250,  # AAD372
        "Krieger": 13015917,  # C69B6D
        "Magier": 4179947,  # 3FC7EB
        "Mönch": 65432,  # 00FF98
        "Paladin": 16026810,  # F48CBA
        "Priester": 16777215,  # FFFFFF
        "Rufer": 3380095,  # 33937F
        "Schamane": 28893,  # 0070DD
        "Schurke": 16774248,  # FFF468
        "Todesritter": 12852794  # C41E3A
    }

    if classname in colordict:
        color = colordict[classname]
    else:
        color = 0
    return color


def make_embed(embeddict: dict) -> discord.Embed:
    """
    Converts a dictionary to a discord Embed object
    :param embeddict: A dictionary in the format of a discord Embed
    :return: Discord Embed object made from the input dictionary
    """
    return discord.Embed().from_dict(embeddict)


def eval_gear_status(status: int) -> str:
    """
    Looks up a status ID
    :param status: A ID representing the status of an Item
    :return: A string containing an emote representing the status
    """
    match status:
        case 0:
            status_string = f"{settings['emotes']['checkmark']} "
        case 1:
            status_string = f"{settings['emotes']['warning']} "
        case 2:
            status_string = f"{settings['emotes']['alert']} "
        case 3:
            status_string = f"{settings['emotes']['none']} "
    return status_string


def character_exists(name: str, realm: str) -> bool:
    """
    Checks if a character exists by making a simple api-request
    :param name: Name of the Character
    :param realm: Name of the realm
    :return: Boolean (if character exists or not)
    """
    media = data_processing.get_char_media(name, realm)
    return type(media) is not int


def get_mains() -> list:
    """
    Reads the list of User-Mains from a file
    :return:List of User-Mains
    """
    file = open("playermains.json", "r")
    mainlist = json.load(file)
    file.close()
    return mainlist


def save_mains(mainlist: list):
    """
    Saves list of User-Mains to a file
    :param mainlist: List of User-Mains
    """
    file = open("playermains.json", "w")
    json.dump(mainlist, file, indent=4)
    file.close()


def remove_main(discord_id: int):
    """
    Removes the main of a given User from the Mainslist
    :param discord_id: DiscordID of the user in question
    """
    mainlist = get_mains()
    if str(discord_id) in mainlist:
        del mainlist[str(discord_id)]
    save_mains(mainlist)


def remove_raid(discord_id: int):
    """
    Removes all character with the ID of a given User from the Raidlist
    :param discord_id: DiscordID of the User in question
    """
    raidliste = get_raidlist()
    dellist = []
    for character in raidliste:
        if str(discord_id) == character["discordID"]:
            dellist.append(character)

    if len(dellist) != 0:
        for character in dellist:
            raidliste.remove(character)
    save_raidlist(raidliste)


def get_item_icon_id(item_id: int) -> int:
    """
    Checks if the given Item ID already has a Icon ID saved and saves it if not
    :param item_id: ID of the Item in question
    :return: A list with the url of an icon if it hasn't been saved yet, and the ID of the ICon
    """
    file = open("itemiconid.json", "r")
    itemiconidlist = json.load(file)
    file.close()

    if str(item_id) in itemiconidlist:
        icondata = ["", itemiconidlist[str(item_id)]]
    else:
        icondata = data_processing.get_item_media(item_id)
        itemiconidlist[str(item_id)] = icondata[1]

    file = open("itemiconid.json", "w")
    json.dump(itemiconidlist, file, indent=4)
    file.close()

    return icondata


#
#       Async Functions
#

async def add_role(guild: discord.Guild, member: discord.Member, roleid: int):
    """
    Adds a given role to a given Member of a guild
    :param guild: The Guild with the Member for which to add a role
    :param member: The Member to add a role to
    :param roleid: The ID of the Role to be added
    """
    role = await guild.fetch_role(roleid)
    await member.add_roles(role)


async def remove_role(guild: discord.Guild, member: discord.Member, roleid: int):
    """
    Removes a given role from a given Member of a guild
    :param guild: The Guild with the Member for which to remove a role
    :param member: The Member to remove a role from
    :param roleid: The ID of the Role to be removed
    """
    role = await guild.fetch_role(roleid)
    await member.remove_roles(role)


async def get_member(guild: discord.Guild, member_id: int) -> discord.Member:
    """
    Looks up a User ID in a guild to get the corresponding Member Object
    :param guild: The Guild in which the member is
    :param member_id: The ID of the member in question
    :return:Discord Member object of the requested Member
    """
    member = await guild.fetch_member(member_id)
    return member


async def get_username(guild: discord.Guild, member_id: int) -> str:
    """
    Looks up a User ID in a guild to get the correspending Display-name
    :param guild: The Guild in which the member is
    :param member_id: The ID of the member in question
    :return: The Display-name of the User in the Guild
    """
    user = await guild.fetch_member(member_id)
    return user.display_name


async def create_emoji(name: str, url: str) -> discord.Emoji:
    """
    Uploads a Emote to the bot, which the bot can then use
    :param name: Name of the emote
    :param url: Url from which to take the image from
    :return: Discord Emoji Object of the just uploaded Emote
    """
    image = requests.get(url)
    emote = await client.create_application_emoji(name=name, image=image.content)
    return emote


async def get_item_emote(itemid: int) -> str:
    """
    Looks up the emotestring for the icon of an item and creates it if it doesn't exist yet
    :param itemid: ID of the Item in question
    :return: The emotestring so the bot can use this emote in a message
    """
    icondata = get_item_icon_id(itemid)
    if str(icondata[1]) in settings["emotes"]:
        return settings["emotes"][str(icondata[1])]
    else:
        itememote = await create_emoji(str(icondata[1]), icondata[0])
        settings["emotes"][str(icondata[1])] = str(itememote)
        save_settings(settings)
        return settings["emotes"][str(icondata[1])]


async def construct_gearembed(name: str, realm: str, chardict: dict) -> discord.Embed:
    """
    Constructs an Embed of the equipment of a given character using a dictionary containing information about it
    :param name: The Name of the Character
    :param realm: The Name of the realm of the Character
    :param chardict: A dictionary conatining information about the equipment of the Character in question
    :return: A Discord Embed Object for the equipment of a single character
    """
    embed = {
        "description": f"# [**{name}-{realm}**](https://worldofwarcraft.blizzard.com/de-de/character/eu/"
                       f"{chardict['realm']}/{chardict['name']}/)\n### Character Ilvl: {chardict['equip']['avgilvl']}",
        "color": class_to_color(chardict["class"]),
        "thumbnail": {
            "url": chardict["thumbnail"]
        },
        "fields": [],
        "author": {
            "name": "GearBot"
        }
    }
    for item in chardict["equip"]["gear"]:
        embed["fields"].append({})
        embed["fields"][-1]["name"] = "__**" + item["slot"] + "**__"
        emote = await get_item_emote(item["id"])
        body = emote + " **" + item["name"] + " - " + str(item["ilvl"]) + " " + item["itemtrack"] + "**\n"

        if item["hassocket"]:
            for socket in item["sockets"]:
                if socket["missing"]:
                    body += f"- Fehlender Sockel {settings['emotes']['warning']}\n"
                else:
                    if socket["hasgem"]:
                        body += f"- {socket['item']} {settings['emotes']['checkmark']}\n"
                    else:
                        body += f"- Fehlender Stein {settings['emotes']['alert']}\n"

        if item["hasenchantment"]:
            vz = item["enchantment"][0]
            if vz["missing"]:
                body += f"- Fehlende Verzauberung {settings['emotes']['alert']}\n"
            else:
                if ((item["slot"] == "Schildhand" and item["type"] in ["WEAPON", "TWOHWEAPON"])
                        or item["slot"] != "Schildhand"):
                    match vz["tier"]:
                        case "Tier3":
                            tieremoji = settings['emotes']['t3']
                        case "Tier2":
                            tieremoji = settings['emotes']['t2']
                        case "Tier1":
                            tieremoji = settings['emotes']['t1']
                        case _:
                            tieremoji = ""

                    if "item" in vz:
                        if vz["tier"] == "Tier3":
                            body += f"- {vz['item'].title()} {tieremoji} {settings['emotes']['checkmark']}\n"
                        else:
                            body += f"- {vz['item'].title()} {tieremoji} {settings['emotes']['warning']}\n"
                    else:
                        if vz["tier"] == "Tier3":
                            body += f"- {vz['description'].title()} {tieremoji} {settings['emotes']['checkmark']}\n"
                        else:
                            body += f"- {vz['description'].title()} {tieremoji} {settings['emotes']['warning']}\n"
                else:
                    pass

        if item["hasembellishment"]:
            body += f"- Verziert\n"
        body += "\n"

        embed["fields"][-1]["value"] = body

    embed["fields"].append({"name": ""})

    match chardict["equip"]["embellishments"]:
        case 2:
            embed["fields"][-1]["value"] = \
                f"{settings["emotes"]["embellishment"]}**(2/2)** Verzierungen {settings['emotes']['checkmark']}"
        case 1:
            embed["fields"][-1]["value"] = \
                f"{settings["emotes"]["embellishment"]}**(1/2)** Verzierungen {settings['emotes']['warning']}"
        case 0:
            embed["fields"][-1]["value"] = \
                f"{settings["emotes"]["embellishment"]}**(0/2)** Verzierungen {settings['emotes']['warning']}"
        case _:
            pass

    embed = make_embed(embed)
    return embed


async def check_gear_stats(name: str, realm: str, chardict: dict) -> dict:
    """
    Constructs a dictionary for a field in an embed containing a clear overview over the equipment of a single character
    :param name: Name of the Character
    :param realm: Name of the Realm of the Character
    :param chardict: A dictionary conatining information about the equipment of the Character in question
    :return: Dictionary in the format of a field in a discord embed
    """
    field = {
        "name": f"**{name}-{realm}**"
    }
    body = "🇭 🇳 🇸 🇨 🇧 🇱 🇫 🇼 🇬 🇷 🇷 🇹 🇹 🇺 🇲 🇴 🇻\n"
    for item in chardict["equip"]["gear"]:

        status = 0
        if item["hassocket"]:
            for socket in item["sockets"]:
                if socket["missing"]:
                    if status < 1:
                        status = 1
                else:
                    if socket["hasgem"]:
                        pass
                    else:
                        status = 2

        if item["hasenchantment"]:
            vz = item["enchantment"][0]
            if vz["missing"]:
                status = 2
            else:
                if ((item["slot"] == "Schildhand" and item["type"] in ["WEAPON", "TWOHWEAPON"])
                        or item["slot"] != "Schildhand"):
                    if "item" in vz:
                        if vz["tier"] == "Tier3":
                            pass
                        else:
                            if status < 1:
                                status = 1
                    else:
                        if vz["tier"] == "Tier3":
                            pass
                        else:
                            if status < 1:
                                status = 1
                else:
                    pass

        body += eval_gear_status(status)

    if not chardict["equip"]["hasshield"]:
        body += eval_gear_status(3)

    match chardict["equip"]["embellishments"]:
        case 2:
            body += eval_gear_status(0)
        case 1:
            body += eval_gear_status(1)
        case 0:
            body += eval_gear_status(1)
        case _:
            pass
    field["value"] = body

    return field


async def gear_cmd(message):
    """
    Checks if the command was used correctly and if so, sends an embed with an overview of the specified character
    :param message: The Message that was sent by the User
    """
    args = message.content.split(" ")[1:]
    if len(args) == 0:
        await message.channel.send(
            "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!gear Charactername Realmname\n\
!gear @User```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
        return
    if args[0][0] == "<":
        use_discord_id = True
        discord_id = args[0][2:-1]
        mainlist = get_mains()
        if discord_id in mainlist:
            name = mainlist[discord_id]["name"]
            realm = mainlist[discord_id]["realm"]
        else:
            await message.channel.send("Dieser Benutzer hat keinen eingetragenen Main-Character.")
            return
    else:
        use_discord_id = False
        name = args[0]
        realm = " ".join(args[1:])
    if len(args) < 2 and not use_discord_id:
        await message.channel.send(
            "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!gear Charactername Realmname\n\
!gear @User```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
        return
    await message.channel.send("Sammle Spielerdaten...\nDies kann kurz dauern")
    clean_name = name.lower()
    clean_realm = "-".join(realm.split(" ")).lower().replace("'", "")
    equip = data_processing.get_char_equip(clean_name, clean_realm)
    try:
        int(equip)
        if equip == 404:
            await message.channel.send(f"{name}-{realm} wurde nicht gefunden.\n\
Bitte überprüfe die Schreibweise des Character- und Realmnamens.")
    except TypeError:
        equip["class"] = data_processing.get_char_class(clean_name, clean_realm)
        equip["thumbnail"] = data_processing.get_char_media(clean_name, clean_realm)["portrait"]
        gearembed = await construct_gearembed(name, realm, equip)
        await message.channel.send(embed=gearembed)


async def raidcheck_cmd(message):
    """
    Checks if the command was used correctly and if so, send embeds with a small overview of all characters equipment
    that are in the raidlist
    :param message: Message that was sent by the user
    """
    cleanlist = get_raidlist()
    if len(cleanlist) == 0:
        await message.channel.send("Die Spielerliste ist leer.")
        return
    await message.channel.send("Sammle Spielerdaten...\nDies kann kurz dauern")
    global last_raidcheck_result
    last_raidcheck_result = []
    fields = []
    embedlist = []
    pinglist = []
    x = 0
    for character in cleanlist:
        name = character["name"]
        realm = character["realm"]
        if x == 5:
            if len(embedlist) == 0:
                embed = {
                    "description": "# Raid Gear-Check",
                    "fields": fields,
                    "author": {
                        "name": "Gearbot"
                    },
                    "color": 7929967
                }
            else:
                embed = {
                    "fields": fields,
                    "color": 7929967
                }
            embedlist.append(make_embed(embed))
            last_raidcheck_result.append(data_processing.get_char_equip(
                                        name.lower(),
                                        "-".join(realm.split(" ")).lower().replace("'", "")
            ))
            fields = [await check_gear_stats(name, realm, last_raidcheck_result[-1])]
            if "alert" in fields[-1]["value"] and character["discordID"] != -1:
                pinglist.append(character["discordID"])
            x = 1
        else:
            last_raidcheck_result.append(data_processing.get_char_equip(
                                        name.lower(),
                                        "-".join(realm.split(" ")).lower().replace("'", "")
            ))
            fields.append(await check_gear_stats(name, realm, last_raidcheck_result[-1]))
            if "alert" in fields[-1]["value"] and character["discordID"] != -1:
                pinglist.append(character["discordID"])
            x += 1

    if len(fields) > 0:
        if len(embedlist) == 0:
            embed = {
                "description": "# Raid Gear-Check",
                "fields": fields,
                "author": {
                    "name": "Gearbot"
                },
                "color": 7929967
            }
        else:
            embed = {
                "fields": fields,
                "color": 7929967
            }
        embedlist.append(make_embed(embed))

    embednum = 0
    first = True
    for embed in embedlist:
        embednum += 1
        if embednum == len(embedlist):
            if first:
                first = False
                pingtext = ""
                for discordID in pinglist:
                    pingtext += "<@" + str(discordID) + ">"
                await message.channel.send(pingtext,
                                           embed=embed,
                                           view=SelectView(
                                               select=CharSelect(get_charnames_from_raidlist(get_raidlist()))))
            else:
                await message.channel.send(embed=embed,
                                           view=SelectView(
                                               select=CharSelect(get_charnames_from_raidlist(get_raidlist()))))
        else:
            if first:
                first = False
                pingtext = ""
                for discordID in pinglist:
                    pingtext += "<@" + str(discordID) + ">"
                await message.channel.send(pingtext, embed=embed)
            else:
                await message.channel.send(embed=embed)


async def raidadd_cmd(message):
    """
    Checks if the command was used correctly and if so, adds the specified character to the raidlist
    :param message: Message that was sent by the user
    """
    args = message.content.split(" ")[1:]
    if len(args) == 0:
        await message.channel.send(
            "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!raidadd Charactername Realmname\n\
!raidadd @User\n\
!raidadd @User Charactername Realmname```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
        return
    if args[0][0] == "<":
        use_discord_id = True
        discord_id = args[0][2:-1]
        if len(args) == 1:
            mainlist = get_mains()
            if discord_id in mainlist:
                name = mainlist[discord_id]["name"]
                realm = mainlist[discord_id]["realm"]
            else:
                await message.channel.send("Dieser User hat keinen eingetragenen Main-Charakter")
                return
        else:
            if len(args) < 3:
                await message.channel.send(
                    "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!raidadd Charactername Realmname\n\
!raidadd @User\n!raidadd @User Charactername Realmname```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
                return
            name = args[1]
            realm = " ".join(args[2:])
    else:
        use_discord_id = False
        if len(args) < 2:
            await message.channel.send(
                "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!raidadd Charactername Realmname\n\
!raidadd @User\n!raidadd @User Charactername Realmname```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
            return
        discord_id = -1
        name = args[0]
        realm = " ".join(args[1:])
    clean_name = name.lower()
    clean_realm = "-".join(realm.split(" ")).lower().replace("'", "")

    if not character_exists(clean_name, clean_realm):
        await message.channel.send(f"{name}-{realm} wurde nicht gefunden.\n\
Bitte überprüfe die Schreibweise des Character- und Realmnamens.")
        return

    playerlist = get_raidlist()

    for character in playerlist:
        if name == character["name"] and realm == character["realm"]:
            await message.channel.send(f"{name}-{realm} ist bereits in der Liste")
            return

    if use_discord_id:
        member = await get_member(message.guild, int(discord_id))
        await add_role(message.guild, member, settings["raidrolle"])

    if character_exists(clean_name, clean_realm):
        playerlist.append({"name": name, "realm": realm, "discord_id": discord_id})
        save_raidlist(playerlist)
        await message.channel.send(f"{name}-{realm} wurde der Raidliste hinzugefügt")
    else:
        await message.channel.send(f"""{name}-{realm} wurde nicht gefunden.\n
            Bitte überprüfe die Schreibweise des Character- und Realmnamens.""")


async def raidremove_cmd(message):
    """
    Checks if the command was used correctly and if so, removes the specified character from the raidlist
    :param message: Message that was sent by the user
    """
    args = message.content.split(" ")[1:]
    if len(args) == 0:
        await message.channel.send(
            "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!rairemove Charactername Realmname\n\
!raidremove @User```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
        return
    playerlist = get_raidlist()
    deletelist = []
    if args[0][0] == "<":
        use_discord_id = True
        discord_id = args[0][2:-1]
        for character in playerlist:
            if discord_id == character["discord_id"]:
                deletelist.append(character)
        member = await get_member(message.guild, int(discord_id))
        await remove_role(message.guild, member, settings["raidrolle"])
    else:
        if len(args) < 2:
            await message.channel.send(
                "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!rairemove Charactername Realmname\n\
!raidremove @User```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
            return
        realm = " ".join(args[1:])
        name = args[0]
        use_discord_id = False
        isconnected = False
        for character in playerlist:
            if name.lower() == character["name"].lower() and realm.lower() == character["realm"].lower():
                deletelist.append(character)
                if character["discord_id"] != -1:
                    isconnected = True
                    discord_id = character["discord_id"]
    if len(deletelist) == 0:
        if use_discord_id:
            await message.channel.send(f"<@{discord_id}> hat keine Charactere in der Liste")
        else:
            await message.channel.send(f"{name}-{realm} ist nicht in der Liste")
        return
    for character in deletelist:
        await message.channel.send(f"{character['name']}-{character['realm']} wurde aus der Raidliste entfernt")
        playerlist.remove(character)
    if not use_discord_id and isconnected:
        stillin = False
        for character in playerlist:
            if discord_id == character["discord_id"]:
                stillin = True
        if not stillin:
            member = await get_member(message.guild, int(discord_id))
            await remove_role(message.guild, member, settings["raidrolle"])
    save_raidlist(playerlist)


async def raidlist_cmd(message):
    """
    Checks if the command was used correctly and if so, lists all character that are in the raidlist
    :param message: Message that was sent by the user
    """
    playerlist = get_raidlist()
    text = "# Raid Spielerliste\n\n"

    if len(playerlist) == 0:
        text += "Die Liste ist aktuell leer"

    for character in playerlist:
        if character["discordID"] == -1:
            text += f"{settings['emotes']['discord']}: \
                      {settings['emotes']['cross']} | \
                      **{character['name']}-{character['realm']}**\n"
        else:
            text += f"{settings['emotes']['discord']}: \
                      {settings['emotes']['checkmark']} | \
                      **{character['name']}-{character['realm']}**\n"

    embed = make_embed({
        "description": text,
        "author": {
            "name": "Gearbot"
        },
        "color": 7929967
    })

    await message.channel.send(embed=embed)


async def main_cmd(message):
    """
    Checks if the command was used correctly and if so, tells the user their main, or lets them set one
    :param message: Message that was sent by the user
    """
    args = message.content.split(" ")[1:]
    discord_id = str(message.author.id)
    mainlist = get_mains()
    if len(args) == 0:
        if discord_id in mainlist:
            await message.channel.send(f"Dein Main ist \
**{mainlist[discord_id]["name"]}-{mainlist[discord_id]["realm"]}**")
            return
        else:
            await message.channel.send("Du hast noch keinen eigetragenen Main.\n\
                                       Setze ihn jetzt mit folgendem Befehl:\n\
                                       ```!main Charactername Realmname```")
            return
    if len(args) < 2:
        await message.channel.send(
            "Der Befehl wurde falsch verwendet\n\
Der korrekte Syntax ist\n\
```!main Charactername Realmname```\n\
Bei Realms mit mehreren Wörtern, bitte alle mit Leerzeichen separiert schreiben.\n\
(z.B. \"Der Rat von Dalaran\")")
        return
    name = args[0]
    realm = " ".join(args[1:])
    clean_name = name.lower()
    clean_realm = "-".join(realm.split(" ")).lower().replace("'", "")
    if not character_exists(clean_name, clean_realm):
        await message.channel.send(f"{name}-{realm} wurde nicht gefunden.\n\
Bitte überprüfe die Schreibweise des Character- und Realmnamens.")
        return
    mainlist = get_mains()
    mainlist[discord_id] = {}
    mainlist[discord_id]["name"] = name
    mainlist[discord_id]["realm"] = realm
    save_mains(mainlist)
    await message.channel.send(f"**{name}-{realm}** ist nun dein Main")


async def mainlist_cmd(message):
    """
    Checks if the command was used correctly and if so, lists every main and their corresponding user
    :param message: Message that was sent by the user
    """
    playerlist = get_mains()
    text = "# Main Liste\n\n"

    if len(playerlist) == 0:
        text += "Die Liste ist aktuell leer"

    for discordID, character in playerlist.items():
        username = await get_username(message.guild, discordID)
        text += f"_{username}_ | **{character['name']}-{character['realm']}**\n"

    embed = make_embed({
        "description": text,
        "author": {
            "name": "Gearbot"
        },
        "color": 13414813
    })

    await message.channel.send(embed=embed)


#
#       Discord Events
#

@client.event
async def on_ready():
    """
    Gets executed when the Bot is ready to operate
    """
    print(f'Ready')


@client.event
async def on_message(message):
    """
    Gets executed when a message is sent, checks if a bot command was used
    :param message: The message that was sent
    """
    if message.author == client.user:
        return
    if message.channel.id == settings["gearbotchannel"]:
        if message.content.startswith('!gear'):
            await gear_cmd(message)
            return
    elif message.channel.id == settings["raidchannel"]:
        if message.content.startswith('!raidcheck'):
            await raidcheck_cmd(message)
            return
        elif message.content.startswith('!raidadd'):
            await raidadd_cmd(message)
            return
        elif message.content.startswith('!raidremove'):
            await raidremove_cmd(message)
            return
        elif message.content.startswith('!raidlist'):
            await raidlist_cmd(message)
            return
    elif message.channel.id == settings["mainschannel"]:
        if message.content.startswith('!main') and not message.content.startswith('!mainlist'):
            await main_cmd(message)
            return
        elif message.content.startswith('!mainlist'):
            await mainlist_cmd(message)
            return


@client.event
async def on_member_remove(member):
    """
    Gets executed when a member leaves
    :param member:
    """
    remove_main(member.id)
    remove_raid(member.id)


f = open("token.txt", "r")
token = f.read()
f.close()

settings = load_settings()
print(settings["branch"])
print(discord.__version__ + " - " + discord.version_info.releaselevel)

client.run(token)
save_settings(settings)
