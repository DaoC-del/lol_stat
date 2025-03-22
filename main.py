from lcu_driver import Connector
import pandas as pd

QUEUE_TYPE = {
    420: '单双排',
    440: '灵活组牌',
    450: '极地大乱斗',
    430: '匹配',
    1090: '斗魂竞技场',
    900: 'URF',
}

EXCLUDE_QUEUE_IDS = {4}
connector = Connector()

def parse_match_details(raw: dict) -> dict:
    game_id = raw['gameId']
    game = {
        'gameId': game_id,
        'gameCreationDate': raw.get('gameCreationDate'),
        'gameDuration': raw.get('gameDuration'),
        'matchType': QUEUE_TYPE.get(raw.get('queueId'), 'Unknown'),
    }
    identities = [{
        'gameId': game_id,
        'participantId': ident['participantId'],
        'summonerName': ident['player'].get('gameName'),
    } for ident in raw['participantIdentities']]

    participants = []
    for p in raw['participants']:
        s = p['stats']
        participants.append({
            'gameId': game_id,
            'participantId': p['participantId'],
            'summonerName': next(i['summonerName'] for i in identities if i['participantId'] == p['participantId']),
            'championId': p['championId'],
            'win': s.get('win'),
            'kills': s.get('kills'),
            'deaths': s.get('deaths'),
            'assists': s.get('assists'),
            'KDA': round((s.get('kills',0)+s.get('assists',0))/max(1,s.get('deaths',1)),2),
            'totalDamageDealtToChampions': s.get('totalDamageDealtToChampions'),
            'damageSelfMitigated': s.get('damageSelfMitigated'),
            'totalDamageTaken': s.get('totalDamageTaken'),
            'visionScore': s.get('visionScore'),
            'timeCCingOthers': s.get('timeCCingOthers'),
            'goldEarned': s.get('goldEarned'),
        })

    teams, bans = [], []
    for team in raw['teams']:
        teams.append({
            'gameId': game_id,
            'teamId': team['teamId'],
            'win': team.get('win'),
            'riftHeraldKills': team.get('riftHeraldKills'),
            'baronKills': team.get('baronKills'),
            'dragonKills': team.get('dragonKills'),
        })
        for ban in team.get('bans', []):
            bans.append({
                'gameId': game_id,
                'teamId': team['teamId'],
                'championId': ban['championId'],
            })

    return {
        'game': [game],
        'participant_identities': identities,
        'participants': participants,
        'teams': teams,
        'bans': bans,
    }

async def get_summoner(connection):
    resp = await connection.request('GET','/lol-summoner/v1/current-summoner')
    return await resp.json()

async def get_match_history(connection, puuid, begIndex, endIndex):
    resp = await connection.request(
        'GET',
        f'/lol-match-history/v1/products/lol/{puuid}/matches',
        params={'begIndex': begIndex, 'endIndex': endIndex}
    )
    if resp.status != 200:
        raise RuntimeError(await resp.text())
    return await resp.json()

async def fetch_all_match_history(connection, puuid, page_size=100):
    all_games = []
    beg = 0
    while True:
        history = await get_match_history(connection, puuid, beg, beg + page_size)
        page = history.get('games', {}).get('games', [])
        print(f"Fetching matches {beg}–{beg+page_size}: got {len(page)} records")
        if not page:
            break
        all_games.extend(page)
        if len(page) < page_size:
            break
        beg += page_size
    return all_games

async def get_current_game(connection):
    phase = await (await connection.request('GET','/lol-gameflow/v1/gameflow-phase')).json()
    if phase != 'None':
        return await (await connection.request('GET','/lol-champ-select/v1/session')).json()
    return None

def filter_solo(df: pd.DataFrame) -> pd.DataFrame:
    return df[df['matchType'] == '单双排']

def filter_aram(df: pd.DataFrame) -> pd.DataFrame:
    return df[df['matchType'] == '极地大乱斗']

def filter_all(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()

@connector.ready
async def connect(connection):
    summoner = await get_summoner(connection)
    puuid = summoner['puuid']
    print(f"Summoner: {summoner['displayName']}")

    games = await fetch_all_match_history(connection, puuid)
    games = [g for g in games if g.get('queueId') not in EXCLUDE_QUEUE_IDS]
    print(f"Total fetched matches: {len(games)}")

    all_entities = {k: [] for k in ['game','participant_identities','participants','teams','bans']}
    for game_raw in games:
        parsed = parse_match_details(game_raw)
        for k, v in parsed.items():
            all_entities[k].extend(v)

    df_game = pd.DataFrame(all_entities['game'])
    df_part = pd.DataFrame(all_entities['participants']).merge(df_game, on='gameId')

    print("\n===== 单双排 =====")
    print(filter_solo(df_part).to_string(index=False))

    print("\n===== 极地大乱斗 =====")
    print(filter_aram(df_part).to_string(index=False))

    print("\n===== 全模式 =====")
    print(filter_all(df_part).to_string(index=False))

    current_game = await get_current_game(connection)
    print("In‑game:" if current_game else "Not in game right now.")
    await connector.stop()

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def on_gameflow_update(connection, event):
    print("Game phase changed →", event.data)

connector.start()
