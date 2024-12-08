"""
blizzapi
~~~~~~~~~~~~

This module implements calls to the Blizzard-API.

"""

from json import JSONDecodeError

import requests
import json

credentials_file = "blizzardapi.txt"
locale = "de_DE"


def get_credentials() -> list:
    """
    Reads both the client_id and the secret from a file

    :return: A list in which the first element is the client_id and the second element is the secret
    """
    file = open(credentials_file, "r")
    credentials = file.read().splitlines()
    file.close()
    return credentials


def get_access_token():
    """
    Uses the client_id and the secret to make a request to the blizzard authentification servers to retrieve
    an accesstoken to make a request to their api

    :return: Either the accesstoken for the api, or the status code of the request if it was not ok
    """
    credentials = get_credentials()
    client_id = credentials[0]
    secret = credentials[1]
    auth_request_data = {"grant_type": "client_credentials"}
    auth_response = requests.post("https://oauth.battle.net/token", data=auth_request_data, auth=(client_id, secret))

    if not auth_response.ok:
        return auth_response.status_code

    try:
        auth_response_content = json.loads(auth_response.text)
        accesstoken = auth_response_content["access_token"]
    except TypeError or JSONDecodeError or KeyError:
        return auth_response.status_code
    return accesstoken


def call_blizz_api(url: str, namespace: str):
    """
    Makes a request to the blizzard api to retrieve information

    :param url: The api-url to make a request to
    :param namespace: The namespace to use for this request
    :return: Either the answer of the api, or the status code of the request if it was not ok
    """
    accesstoken = get_access_token()
    try:
        int(accesstoken)
        return accesstoken
    except ValueError:
        pass

    api_call_header = {
        'Authorization': f'Bearer {accesstoken}',
    }

    api_call_parameters = {
        'namespace': namespace,
        'locale': locale,
    }

    api_response = requests.get(url, params=api_call_parameters, headers=api_call_header)

    if not api_response.ok:
        return api_response.status_code

    try:
        api_response_json = json.loads(api_response.text)
    except TypeError or JSONDecodeError:
        return api_response.status_code

    return api_response_json


def get_character_info(name: str, realm: str, infotype: str):
    """
    Constructs a url for the information requested and then forwards it to
    call_blizz_api()

    :param name: Name of the character for which to get information
    :param realm: Name of the Realm of the Character
    :param infotype: The type of information you would like to retrieve
    :return: The answer of the api
    """
    print(f"Making Characterinfo request of type: \"{infotype}\" for \"{name}-{realm}\"")
    url = f"https://eu.api.blizzard.com/profile/wow/character/{realm}/{name}/{infotype}"
    return call_blizz_api(url, "profile-eu")


def getitemmedia(itemid: int):
    """
    Constructs a url for the information requested and then forwards it to
    call_blizz_api()

    :param itemid: The ID of the Item for which to make a request
    :return: The answer of the api
    """
    print(f"Making Item-media request for ID: {itemid}")
    url = f"https://eu.api.blizzard.com/data/wow/media/item/{itemid}"
    return call_blizz_api(url, "static-eu")
