from lcu_driver import Connector

connector = Connector()

async def get_summoner(connection):
    resp = await connection.request('GET', '/lol-summoner/v1/current-summoner')
    data = await resp.json()
    return data

async def get_ranked_stats(connection, summoner_id):
    resp = await connection.request('GET', f'/lol-ranked/v1/ranked-stats/{summoner_id}')
    return await resp.json()

async def get_match_history(connection, puuid, begIndex=0, endIndex=1):
    params = {"begIndex": begIndex, "endIndex": endIndex}
    resp = await connection.request(
        "GET",
        f"/lol-match-history/v1/products/lol/{puuid}/matches",
        params=params
    )
    print(f"{resp}")
    if resp.status != 200:
        text = await resp.text()
        raise RuntimeError(f"Failed to fetch match history ({resp.status}): {text}")
    return await resp.json()


async def get_current_game(connection):
    resp = await connection.request('GET', '/lol-gameflow/v1/gameflow-phase')
    phase = await resp.json()
    if phase != 'None':
        resp2 = await connection.request('GET', '/lol-champ-select/v1/session')
        return await resp2.json()
    return None

@connector.ready
async def connect(connection):
    summoner = await get_summoner(connection)
    print(f"Summoner: {summoner})")

    # ranked = await get_ranked_stats(connection, summoner['summonerId'])
    # print("Ranked:", ranked.get('queues', 'No ranked data'))

    history = await get_match_history(connection, summoner['puuid'])
    print(f"{history}")
    print(f"Last {len(history)} matches:", [g['gameId'] for g in history])

    current_game = await get_current_game(connection)
    if current_game:
        print("In‑game:", current_game['gameId'])
    else:
        print("Not in game right now.")

    await connector.stop()

@connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
async def on_gameflow_update(connection, event):
    phase = event.data
    print("Game phase changed →", phase)

connector.start()
