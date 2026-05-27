"""
V3_Opponent - A strong bot designed to beat V3_defense bots.
Strategy:
1. Reserve only 20% of ships for defense (more aggressive).
2. Prioritize attacking enemy (player) planets with high production.
3. Skip targets that are too far (>50 units) or have too many defenders (>100 ships).
4. Attack only when we have a decisive advantage (available > defense_strength * 1.5).
5. Simple coordination: each target is assigned to the nearest owned planet.
"""

import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet

RESERVE_RATIO = 0.2          # Only 20% reserved (more aggressive than V3's 30%)
MAX_ATTACK_DISTANCE = 50     # Don't send fleets beyond this distance
MAX_TARGET_SHIPS = 100        # Don't attack planets with >100 garrison (wasteful)
ADVANTAGE_FACTOR = 1.5        # Need 1.5x defender's strength to attack


def agent(obs):
    moves = []
    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    raw_planets = obs.get("planets", []) if isinstance(obs, dict) else obs.planets
    fleets_raw = obs.get("fleets", []) if isinstance(obs, dict) else obs.fleets

    planets = [Planet(*p) for p in raw_planets]

    my_planets = [p for p in planets if p.owner == player]
    neutral_targets = [p for p in planets if p.owner == -1]
    enemy_targets = [p for p in planets if p.owner not in (-1, player)]

    # --- Build a list of candidate targets with priority score ---
    candidates = []
    for target in enemy_targets + neutral_targets:
        if target.ships > MAX_TARGET_SHIPS:
            continue
        if target.owner != -1:  
            priority = (target.production ** 2) * 10
        else: 
            priority = target.production  
        candidates.append((target, priority))

    if not candidates:
        return moves

    # --- Sort candidates by priority (highest first) ---
    candidates.sort(key=lambda x: x[1], reverse=True)

    # --- For each of my planets, decide action ---
    assigned_targets = set()

    for mine in my_planets:
        reserve = int(mine.ships * RESERVE_RATIO)
        available = mine.ships - reserve
        if available < 1:
            continue

        best_target = None
        best_score = -1
        for target, priority in candidates:
            if target.id in assigned_targets:
                continue  

            distance = math.hypot(target.x - mine.x, target.y - mine.y)
            if distance > MAX_ATTACK_DISTANCE:
                continue

            defense = target.ships

            ships_needed = defense + 1

            if available >= ships_needed * ADVANTAGE_FACTOR:
                score = priority / (distance + 1)
                if score > best_score:
                    best_score = score
                    best_target = target

        if best_target is None:
            continue

        ships_needed = best_target.ships + 1
        angle = math.atan2(best_target.y - mine.y, best_target.x - mine.x)
        moves.append([mine.id, angle, ships_needed])
        assigned_targets.add(best_target.id)

    return moves