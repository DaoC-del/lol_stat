import pymysql
import json
from datetime import datetime

DB_NAME = "lol_stats"
DB_USER = "lol_user"
DB_PASS = "lol_pass"
DB_HOST = "localhost"
DB_PORT = 3306

def connect_mysql():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            charset="utf8mb4",
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARSET utf8mb4")
        conn.select_db(DB_NAME)
        return conn
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

def init_tables_if_missing(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            game_id BIGINT PRIMARY KEY,
            game_creation DATETIME,
            duration_sec INT,
            queue_id INT,
            map_id INT,
            game_mode VARCHAR(32),
            game_type VARCHAR(32),
            game_version VARCHAR(32),
            is_fallback BOOLEAN DEFAULT FALSE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            game_id BIGINT,
            team_id SMALLINT,
            win BOOLEAN,
            first_blood BOOLEAN,
            first_tower BOOLEAN,
            first_dragon BOOLEAN,
            first_baron BOOLEAN,
            first_inhibitor BOOLEAN,
            first_rift_herald BOOLEAN,
            tower_kills SMALLINT,
            inhibitor_kills SMALLINT,
            dragon_kills SMALLINT,
            baron_kills SMALLINT,
            rift_herald_kills SMALLINT,
            bans JSON,
            PRIMARY KEY (game_id, team_id),
            FOREIGN KEY (game_id) REFERENCES matches(game_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            puuid CHAR(36) PRIMARY KEY,
            summoner_name VARCHAR(32),
            tag_line VARCHAR(8),
            platform_id VARCHAR(4),
            profile_icon INT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            game_id BIGINT,
            participant_id SMALLINT,
            puuid CHAR(36),
            team_id SMALLINT,
            champion_id SMALLINT,
            spell1_id SMALLINT,
            spell2_id SMALLINT,
            lane VARCHAR(16),
            role VARCHAR(16),
            champ_level SMALLINT,

            kills SMALLINT,
            deaths SMALLINT,
            assists SMALLINT,
            dmg_total INT,
            dmg_magic INT,
            dmg_phys INT,
            dmg_true INT,
            taken_total INT,
            taken_magic INT,
            taken_phys INT,
            taken_true INT,
            heal_total INT,
            units_healed SMALLINT,
            shield_teammates INT,
            cc_time_sec SMALLINT,

            vision_score SMALLINT,
            wards_placed SMALLINT,
            wards_killed SMALLINT,
            detector_wards SMALLINT,

            gold_earned INT,
            gold_spent INT,
            minions_killed SMALLINT,
            jungle_cs SMALLINT,

            item0 INT, item1 INT, item2 INT,
            item3 INT, item4 INT, item5 INT, item6 INT,

            primary_style_id INT,
            sub_style_id INT,
            perk0 INT, perk1 INT, perk2 INT, perk3 INT,
            perk4 INT, perk5 INT,
            stat_perk0 INT, stat_perk1 INT, stat_perk2 INT,

            win BOOLEAN,

            PRIMARY KEY (game_id, participant_id),
            FOREIGN KEY (game_id) REFERENCES matches(game_id),
            FOREIGN KEY (puuid) REFERENCES players(puuid),
            FOREIGN KEY (game_id, team_id) REFERENCES teams(game_id, team_id)
        )
    """)

    conn.commit()

def insert_match_json(match_json: dict, conn, is_fallback=False):
    game_id = match_json["gameId"]
    game_creation = datetime.fromisoformat(
        match_json.get("gameCreationDate", "2000-01-01T00:00:00Z").replace("Z", "+00:00")
    )
    duration = match_json.get("gameDuration", 0)
    mode = match_json.get("gameMode", "")
    gtype = match_json.get("gameType", "")
    queue_id = match_json.get("queueId", 0)
    map_id = match_json.get("mapId", 0)
    version = match_json.get("gameVersion", "")

    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT IGNORE INTO matches (
                game_id, game_creation, duration_sec, queue_id, map_id,
                game_mode, game_type, game_version, is_fallback
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (game_id, game_creation, duration, queue_id, map_id, mode, gtype, version, is_fallback))

        for t in match_json.get("teams", []):
            cursor.execute("""
                INSERT IGNORE INTO teams (
                    game_id, team_id, win, first_blood, first_tower, first_dragon, first_baron,
                    first_inhibitor, first_rift_herald,
                    tower_kills, inhibitor_kills, dragon_kills, baron_kills, rift_herald_kills, bans
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                game_id, t.get("teamId"), t.get("win") == "Win",
                t.get("firstBlood"), t.get("firstTower"), t.get("firstDargon", False), t.get("firstBaron", False),
                t.get("firstInhibitor", False), t.get("firstRiftHerald", False),
                t.get("towerKills", 0), t.get("inhibitorKills", 0), t.get("dragonKills", 0),
                t.get("baronKills", 0), t.get("riftHeraldKills", 0), json.dumps(t.get("bans", []))
            ))

        puuid_map = {
            ident["participantId"]: ident["player"]
            for ident in match_json.get("participantIdentities", [])
        }

        for p in match_json.get("participants", []):
            stats = p.get("stats", {})
            timeline = p.get("timeline", {})
            participant_id = p.get("participantId")
            player = puuid_map.get(participant_id, {})

            puuid = player.get("puuid", "")
            if puuid:
                cursor.execute("""
                    INSERT IGNORE INTO players (puuid, summoner_name, tag_line, platform_id, profile_icon)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    puuid,
                    player.get("summonerName", ""),
                    player.get("tagLine", ""),
                    player.get("platformId", ""),
                    player.get("profileIcon", 0)
                ))

            args = (
                game_id, participant_id, puuid,
                p.get("teamId"), p.get("championId"), p.get("spell1Id"), p.get("spell2Id"),
                timeline.get("lane", ""), timeline.get("role", ""), stats.get("champLevel", 0),
                stats.get("kills", 0), stats.get("deaths", 0), stats.get("assists", 0),
                stats.get("totalDamageDealtToChampions", 0), stats.get("magicDamageDealtToChampions", 0),
                stats.get("physicalDamageDealtToChampions", 0), stats.get("trueDamageDealtToChampions", 0),
                stats.get("totalDamageTaken", 0), stats.get("magicalDamageTaken", 0),
                stats.get("physicalDamageTaken", 0), stats.get("trueDamageTaken", 0),
                stats.get("totalHeal", 0), stats.get("totalUnitsHealed", 0),
                stats.get("totalShieldedOnTeammates", 0), stats.get("timeCCingOthers", 0),
                stats.get("visionScore", 0), stats.get("wardsPlaced", 0), stats.get("wardsKilled", 0),
                stats.get("visionWardsBoughtInGame", 0),
                stats.get("goldEarned", 0), stats.get("goldSpent", 0), stats.get("totalMinionsKilled", 0),
                stats.get("neutralMinionsKilled", 0),
                stats.get("item0", 0), stats.get("item1", 0), stats.get("item2", 0),
                stats.get("item3", 0), stats.get("item4", 0), stats.get("item5", 0), stats.get("item6", 0),
                stats.get("perkPrimaryStyle", 0), stats.get("perkSubStyle", 0),
                stats.get("perk0", 0), stats.get("perk1", 0), stats.get("perk2", 0),
                stats.get("perk3", 0), stats.get("perk4", 0), stats.get("perk5", 0),
                stats.get("statPerk0", 0), stats.get("statPerk1", 0), stats.get("statPerk2", 0),
                stats.get("win", False)
            )

            cursor.execute("""
                INSERT IGNORE INTO participants (
                    game_id, participant_id, puuid, team_id, champion_id,
                    spell1_id, spell2_id, lane, role, champ_level,
                    kills, deaths, assists, dmg_total, dmg_magic, dmg_phys, dmg_true,
                    taken_total, taken_magic, taken_phys, taken_true,
                    heal_total, units_healed, shield_teammates, cc_time_sec,
                    vision_score, wards_placed, wards_killed, detector_wards,
                    gold_earned, gold_spent, minions_killed, jungle_cs,
                    item0, item1, item2, item3, item4, item5, item6,
                    primary_style_id, sub_style_id,
                    perk0, perk1, perk2, perk3, perk4, perk5,
                    stat_perk0, stat_perk1, stat_perk2,
                    win
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s
                )
            """, args)

    conn.commit()
