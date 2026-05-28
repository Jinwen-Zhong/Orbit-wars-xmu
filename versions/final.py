import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet


EARLY_EXPANSION_PLANETS = 3
MIDGAME_STEP = 120
EARLY_RESERVE_RATIO = 0.30
LATE_RESERVE_RATIO = 0.45
LATE_ENEMY_WEIGHT = 1.35


def get_obs(obs, key, default):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def target_score(source, target, player, step):
    distance = math.hypot(target.x - source.x, target.y - source.y)
    enemy_weight = LATE_ENEMY_WEIGHT if target.owner not in (-1, player) and step >= MIDGAME_STEP else 1.0
    return enemy_weight * target.production / (distance + target.ships + 1)


def reserve_for(source, target, my_planet_count, step):
    if target.owner == -1 and my_planet_count <= EARLY_EXPANSION_PLANETS:
        return 0

    ratio = EARLY_RESERVE_RATIO if step < MIDGAME_STEP else LATE_RESERVE_RATIO
    return int(source.ships * ratio)


def agent(obs):
    moves = []

    player = get_obs(obs, "player", 0)
    step = get_obs(obs, "step", 0)
    raw_planets = get_obs(obs, "planets", [])

    planets = [Planet(*p) for p in raw_planets]
    my_planets = [p for p in planets if p.owner == player]
    targets = [p for p in planets if p.owner != player]

    if not my_planets or not targets:
        return moves

    for mine in my_planets:
        best_target = None
        best_score = -1

        for target in targets:
            score = target_score(mine, target, player, step)
            if score > best_score:
                best_score = score
                best_target = target

        if best_target is None:
            continue

        reserve = reserve_for(mine, best_target, len(my_planets), step)
        available = mine.ships - reserve
        ships_needed = best_target.ships + 1

        if available >= ships_needed:
            angle = math.atan2(best_target.y - mine.y, best_target.x - mine.x)
            moves.append([mine.id, angle, ships_needed])

    return moves
