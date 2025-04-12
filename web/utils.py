async def get_current_summoner(connection):
    resp = await connection.request('GET', '/lol-summoner/v1/current-summoner')
    data = await resp.json()
    return data.get('displayName'), data.get('puuid')
