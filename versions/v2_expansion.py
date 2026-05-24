import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet


def agent(obs):
    moves = []

    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    raw_planets = obs.get("planets", []) if isinstance(obs, dict) else obs.planets

    planets = [Planet(*p) for p in raw_planets]

    my_planets = [p for p in planets if p.owner == player]
    targets = [p for p in planets if p.owner != player]

    if not my_planets or not targets:
        return moves

    for mine in my_planets:
        best_target = None
        best_score = -1

        for target in targets:
            distance = math.hypot(target.x - mine.x, target.y - mine.y)
            score = target.production / (distance + target.ships + 1)

            if score > best_score:
                best_score = score
                best_target = target

        if best_target is None:
            continue

        ships_needed = best_target.ships + 1

        if mine.ships >= ships_needed:
            angle = math.atan2(best_target.y - mine.y, best_target.x - mine.x)
            moves.append([mine.id, angle, ships_needed])

    return moves