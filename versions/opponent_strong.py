import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet


def agent(obs):
    moves = []

    # 读取当前玩家编号和星球信息
    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    raw_planets = obs.get("planets", []) if isinstance(obs, dict) else obs.planets

    # 转换为 Planet 对象，方便用 p.owner / p.x / p.ships 等方式访问
    planets = [Planet(*p) for p in raw_planets]

    # 我方星球
    my_planets = [p for p in planets if p.owner == player]

    # 非我方星球：包括中立星球和敌方星球
    targets = [p for p in planets if p.owner != player]

    if not my_planets or not targets:
        return moves

    for mine in my_planets:
        best_target = None
        best_score = -1

        # 遍历所有目标星球，选择价值最高的目标
        for target in targets:
            distance = math.hypot(target.x - mine.x, target.y - mine.y)

            # 强化对手的目标选择逻辑：产量越高越值得打；距离越远、守军越多越不值得打
            score = target.production / (distance + target.ships + 1)

            if score > best_score:
                best_score = score
                best_target = target

        if best_target is None:
            continue

        # 占领目标至少需要比目标守军多 1 艘
        ships_needed = best_target.ships + 1

        # 强化点：保留防守兵力，避免把自己的星球掏空
        reserve = max(5, int(mine.ships * 0.3))

        # 只有在发兵后仍能保留 reserve 时才出兵
        if mine.ships >= ships_needed + reserve:
            angle = math.atan2(best_target.y - mine.y, best_target.x - mine.x)
            moves.append([mine.id, angle, ships_needed])

    return moves