# mappings.py
import logging
import requests

def load_queue_map():
    try:
        resp = requests.get('https://static.developer.riotgames.com/docs/lol/queues.json', timeout=5)
        resp.raise_for_status()
        return {item['queueId']: item['description'] for item in resp.json()}
    except Exception:
        logging.warning("Using fallback queue map.")
        return {420: 'Ranked Solo', 450: 'ARAM', 1700: 'Ascension'}

def load_champion_map():
    try:
        data = requests.get("https://ddragon.leagueoflegends.com/cdn/15.6.1/data/en_US/champion.json", timeout=5).json()['data']
        return {int(v['key']): v['name'] for v in data.values()}
    except Exception:
        logging.warning("Failed to load champion map.")
        return {}
