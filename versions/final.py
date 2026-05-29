import math


BOARD_SIZE = 100.0
CENTER = 50.0
SUN_RADIUS = 10.0
ROTATION_RADIUS_LIMIT = 50.0
EPISODE_STEPS = 500
TAU = 2.0 * math.pi


PARAMS = {
    "reserve_early_min": 2,
    "reserve_early_prod": 2.0,
    "reserve_early_enemy": 1,
    "reserve_mid_min": 4,
    "reserve_mid_prod": 3.0,
    "reserve_mid_enemy": 2,
    "reserve_late_min": 3,
    "reserve_late_prod": 2.0,
    "reserve_late_enemy": 1,
    "reserve_main_min": 7,
    "reserve_main_prod_2p": 4.0,
    "reserve_main_prod_4p": 3.0,
    "reserve_main_enemy": 4,
    "neutral_future": 0.20,
    "neutral_prod": 22.0,
    "neutral_need": 1.15,
    "neutral_eta": 1.35,
    "neutral_early_bonus": 38.0,
    "neutral_mid_bonus": 16.0,
    "enemy_future": 0.16,
    "enemy_prod": 30.0,
    "enemy_garrison": 0.65,
    "enemy_need": 0.88,
    "enemy_eta": 1.75,
    "enemy_early_penalty": 50.0,
    "enemy_2p_bonus": 18.0,
    "enemy_4p_bonus": 6.0,
    "static_bonus": 12.0,
    "moving_eta_penalty": 0.35,
    "moving_penalty_cap": 18.0,
    "close_distance": 18.0,
    "close_bonus": 9.0,
    "threshold_mid": -15.0,
    "threshold_early": -55.0,
    "threshold_late": 8.0,
    "neutral_margin_early": 1,
    "neutral_margin_late": 2,
    "enemy_pressure_2p": 0.76,
    "enemy_pressure_4p": 0.58,
    "enemy_late_pressure_add": 0.14,
    "max_moves_2p": 14,
    "max_moves_4p": 18,
}


def _get(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _pos(planet):
    return (float(planet[2]), float(planet[3]))


def _point_segment_distance(point, start, end):
    sx, sy = start
    ex, ey = end
    px, py = point
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return _dist(point, start)
    t = ((px - sx) * dx + (py - sy) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    return _dist(point, (sx + t * dx, sy + t * dy))


def _crosses_sun(start, end, margin=0.15):
    return _point_segment_distance((CENTER, CENTER), start, end) < SUN_RADIUS + margin


def _fleet_speed(ships, max_speed=6.0):
    ships = max(1, int(ships))
    speed = 1.0 + (max_speed - 1.0) * (math.log(ships) / math.log(1000)) ** 1.5
    return min(speed, max_speed)


def _is_static(planet):
    return _dist(_pos(planet), (CENTER, CENTER)) + float(planet[4]) >= ROTATION_RADIUS_LIMIT


def _future_position(planet, angular_velocity, turns):
    if _is_static(planet):
        return _pos(planet)
    x, y = _pos(planet)
    dx = x - CENTER
    dy = y - CENTER
    orbital_radius = math.hypot(dx, dy)
    if orbital_radius <= 1e-9:
        return (x, y)
    angle = math.atan2(dy, dx) + angular_velocity * max(0.0, turns)
    return (CENTER + orbital_radius * math.cos(angle), CENTER + orbital_radius * math.sin(angle))


def _aim_options(source_pos, target_pos, radius):
    dx = target_pos[0] - source_pos[0]
    dy = target_pos[1] - source_pos[1]
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return [target_pos]
    nx = -dy / length
    ny = dx / length
    points = [target_pos]
    for scale in (0.45, -0.45, 0.85, -0.85):
        points.append((target_pos[0] + nx * radius * scale, target_pos[1] + ny * radius * scale))
    return points


def _blocked_by_planet(source, aim_point, target, planets, comet_ids):
    start = _pos(source)
    target_id = int(target[0])
    source_id = int(source[0])
    total = _dist(start, aim_point)
    if total <= 1e-9:
        return True
    for planet in planets:
        pid = int(planet[0])
        if pid == target_id or pid == source_id or pid in comet_ids:
            continue
        px, py = _pos(planet)
        sx, sy = start
        ex, ey = aim_point
        vx = ex - sx
        vy = ey - sy
        projection = ((px - sx) * vx + (py - sy) * vy) / (total * total)
        if projection <= 0.04 or projection >= 0.98:
            continue
        if _point_segment_distance((px, py), start, aim_point) <= float(planet[4]) + 0.15:
            return True
    return False


def _aim_at(source, target, ships, planets, comet_ids, angular_velocity):
    start = _pos(source)
    speed = _fleet_speed(ships)
    future = _pos(target)
    eta = _dist(start, future) / speed
    for _ in range(4):
        future = _future_position(target, angular_velocity, eta)
        eta = _dist(start, future) / speed

    for aim_point in _aim_options(start, future, float(target[4])):
        if _crosses_sun(start, aim_point):
            continue
        if _blocked_by_planet(source, aim_point, target, planets, comet_ids):
            continue
        return math.atan2(aim_point[1] - start[1], aim_point[0] - start[0]), eta, aim_point
    return None, eta, future


def _ray_will_hit_planet(fleet, planet, margin=0.9):
    fx, fy = float(fleet[2]), float(fleet[3])
    angle = float(fleet[4])
    px, py = _pos(planet)
    vx = math.cos(angle)
    vy = math.sin(angle)
    dx = px - fx
    dy = py - fy
    forward = dx * vx + dy * vy
    if forward <= 0.0:
        return False
    closest_sq = dx * dx + dy * dy - forward * forward
    return closest_sq <= (float(planet[4]) + margin) ** 2


def _incoming_ships(planets, fleets, comet_ids):
    incoming = {int(p[0]): {} for p in planets}
    for fleet in fleets:
        owner = int(fleet[1])
        ships = int(fleet[6])
        best_pid = None
        best_forward = 10**9
        fx, fy = float(fleet[2]), float(fleet[3])
        vx = math.cos(float(fleet[4]))
        vy = math.sin(float(fleet[4]))
        for planet in planets:
            if int(planet[0]) in comet_ids:
                continue
            if not _ray_will_hit_planet(fleet, planet):
                continue
            px, py = _pos(planet)
            forward = (px - fx) * vx + (py - fy) * vy
            if forward < best_forward:
                best_forward = forward
                best_pid = int(planet[0])
        if best_pid is not None:
            incoming[best_pid][owner] = incoming[best_pid].get(owner, 0) + ships
    return incoming


def _raw_need(target, player, eta, incoming):
    owner = int(target[1])
    garrison = int(target[5])
    production = int(target[6])
    mine = incoming.get(player, 0)
    enemy = sum(v for k, v in incoming.items() if k != player)
    if owner == -1:
        return garrison + enemy - mine + 1
    future = garrison + production * min(45, max(0, int(eta)))
    return future + enemy - mine + 2


def _reserve_for(source, incoming, player, step, num_players):
    p = PARAMS
    ships = int(source[5])
    production = int(source[6])
    enemy_incoming = sum(v for owner, v in incoming.get(int(source[0]), {}).items() if owner != player)

    if step < 45:
        reserve = max(p["reserve_early_min"], production * p["reserve_early_prod"], enemy_incoming + p["reserve_early_enemy"])
    elif step < 130:
        reserve = max(p["reserve_mid_min"], production * p["reserve_mid_prod"], enemy_incoming + p["reserve_mid_enemy"])
    elif step > 420:
        reserve = max(p["reserve_late_min"], production * p["reserve_late_prod"], enemy_incoming + p["reserve_late_enemy"])
    else:
        prod_mult = p["reserve_main_prod_2p"] if num_players == 2 else p["reserve_main_prod_4p"]
        reserve = max(p["reserve_main_min"], production * prod_mult, enemy_incoming + p["reserve_main_enemy"])

    return min(ships, int(reserve))


def _count_players(planets, player):
    owners = [int(p[1]) for p in planets if int(p[1]) >= 0]
    return max(owners + [player]) + 1


def _target_score(source, target, player, incoming, angular_velocity, step, num_players, planets, comet_ids):
    p = PARAMS
    owner = int(target[1])
    remaining = EPISODE_STEPS - step
    source_pos = _pos(source)
    target_pos = _pos(target)
    rough_distance = _dist(source_pos, target_pos)
    rough_eta = rough_distance / _fleet_speed(max(8, int(target[5]) + 2))
    rough_need = max(1, _raw_need(target, player, rough_eta, incoming))
    angle, eta, _ = _aim_at(source, target, rough_need, planets, comet_ids, angular_velocity)
    if angle is None:
        return -10**9, rough_need, eta, None
    if eta > remaining - 4:
        return -10**9, rough_need, eta, None

    need = max(1, _raw_need(target, player, eta, incoming))
    production = int(target[6])
    garrison = int(target[5])
    static_bonus = p["static_bonus"] if _is_static(target) else 0.0
    moving_penalty = 0.0 if _is_static(target) else min(p["moving_penalty_cap"], eta * p["moving_eta_penalty"])
    future_income = production * max(0.0, remaining - eta)

    if owner == -1:
        score = future_income * p["neutral_future"] + production * p["neutral_prod"] - need * p["neutral_need"] - eta * p["neutral_eta"]
        if step < 80:
            score += p["neutral_early_bonus"]
        elif step < 170:
            score += p["neutral_mid_bonus"]
    else:
        score = future_income * p["enemy_future"] + production * p["enemy_prod"] + garrison * p["enemy_garrison"] - need * p["enemy_need"] - eta * p["enemy_eta"]
        if step < 85:
            score -= p["enemy_early_penalty"]
        if num_players == 2:
            score += p["enemy_2p_bonus"]
        else:
            score += p["enemy_4p_bonus"]

    score += static_bonus - moving_penalty
    if rough_distance < p["close_distance"]:
        score += p["close_bonus"]
    return score, need, eta, angle


def _make_move(source, target, send, planets, comet_ids, angular_velocity):
    angle, _, _ = _aim_at(source, target, send, planets, comet_ids, angular_velocity)
    if angle is None:
        return None
    return [int(source[0]), float(angle % TAU), int(send)]


def agent(obs, config=None):
    p = PARAMS
    player = int(_get(obs, "player", 0))
    planets = list(_get(obs, "planets", []) or [])
    fleets = list(_get(obs, "fleets", []) or [])
    comet_ids = set(int(pid) for pid in (_get(obs, "comet_planet_ids", []) or []))
    angular_velocity = float(_get(obs, "angular_velocity", 0.0) or 0.0)
    step = int(_get(obs, "step", 0) or 0)
    num_players = _count_players(planets, player)

    my_planets = [p for p in planets if int(p[1]) == player and int(p[0]) not in comet_ids]
    if not my_planets:
        return []

    incoming = _incoming_ships(planets, fleets, comet_ids)
    moves = []
    committed = {}

    my_planets.sort(key=lambda p: (int(p[5]) - _reserve_for(p, incoming, player, step, num_players), int(p[6])), reverse=True)

    # Reinforce planets that are likely to be flipped by incoming fleets.
    threatened = []
    for planet in my_planets:
        pid = int(planet[0])
        enemy = sum(v for owner, v in incoming.get(pid, {}).items() if owner != player)
        mine = incoming.get(pid, {}).get(player, 0)
        danger = enemy - mine - int(planet[5]) - int(planet[6]) * 4
        if danger > 0:
            threatened.append((danger, planet))
    threatened.sort(reverse=True, key=lambda item: item[0])

    used_sources = set()
    for danger, target in threatened[:3]:
        need = int(danger + 3)
        for source in my_planets:
            sid = int(source[0])
            if sid == int(target[0]) or sid in used_sources:
                continue
            reserve = _reserve_for(source, incoming, player, step, num_players)
            available = int(source[5]) - reserve - committed.get(sid, 0)
            if available < max(6, need):
                continue
            send = min(available, need)
            move = _make_move(source, target, send, planets, comet_ids, angular_velocity)
            if move is not None:
                moves.append(move)
                committed[sid] = committed.get(sid, 0) + send
                used_sources.add(sid)
                break

    targets = [
        p
        for p in planets
        if int(p[1]) != player and int(p[0]) not in comet_ids
    ]
    if not targets:
        return moves

    claimed = {}
    max_moves = int(p["max_moves_4p"] if num_players == 4 else p["max_moves_2p"])

    for source in my_planets:
        sid = int(source[0])
        if sid in used_sources:
            continue
        reserve = _reserve_for(source, incoming, player, step, num_players)
        available = int(source[5]) - reserve - committed.get(sid, 0)
        if available < 4:
            continue

        best = None
        best_score = -10**9
        best_need = 0
        best_angle = None

        for target in targets:
            tid = int(target[0])
            target_incoming = dict(incoming.get(tid, {}))
            if claimed.get(tid, 0):
                target_incoming[player] = target_incoming.get(player, 0) + claimed[tid]
            score, need, _, angle = _target_score(
                source,
                target,
                player,
                target_incoming,
                angular_velocity,
                step,
                num_players,
                planets,
                comet_ids,
            )
            if need <= 0:
                continue
            if score > best_score:
                best = target
                best_score = score
                best_need = int(need)
                best_angle = angle

        if best is None or best_angle is None:
            continue

        threshold = p["threshold_mid"]
        if step < 70:
            threshold = p["threshold_early"]
        elif step > 380:
            threshold = p["threshold_late"]
        if best_score < threshold:
            continue

        owner = int(best[1])
        if owner == -1:
            margin = p["neutral_margin_early"] if step < 120 else p["neutral_margin_late"]
            send = min(available, best_need + margin)
        else:
            pressure = p["enemy_pressure_2p"] if num_players == 2 else p["enemy_pressure_4p"]
            if step > 360:
                pressure += p["enemy_late_pressure_add"]
            send = min(available, max(best_need + 4, int(available * pressure)))

        if send < best_need or send < 4:
            continue

        moves.append([sid, float(best_angle % TAU), int(send)])
        committed[sid] = committed.get(sid, 0) + int(send)
        claimed[int(best[0])] = claimed.get(int(best[0]), 0) + int(send)

        if len(moves) >= max_moves:
            break

    return moves
