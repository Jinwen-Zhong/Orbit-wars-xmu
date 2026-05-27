"""
Final Heuristic Bot for Orbit Wars
Combines: dynamic reserve, enemy prioritization, orbit prediction,
sun avoidance, travel production estimation, and target coordination.
"""

import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet, Fleet, CENTER, ROTATION_RADIUS_LIMIT

# ---------- Configuration ----------
BASE_RESERVE_RATIO = 0.2          
MIN_ABSOLUTE_RESERVE = 8          
SUN_RADIUS = 10.0                 
MAX_ATTACK_DISTANCE = 60          
MAX_TARGET_SHIPS = 120            
ADVANTAGE_FACTOR = 1.3            
THREAT_DISTANCE = 40              

# -----------------------------------

def agent(obs):
    player = obs.get("player", 0) if isinstance(obs, dict) else obs.player
    raw_planets = obs.get("planets", []) if isinstance(obs, dict) else obs.planets
    raw_fleets = obs.get("fleets", []) if isinstance(obs, dict) else obs.fleets
    
    planets = [Planet(*p) for p in raw_planets]
    fleets = [Fleet(*f) for f in raw_fleets]
    
    sun_center = CENTER
    
    initial_planets = [Planet(*p) for p in obs.get("initial_planets", [])]
    angular_velocity = obs.get("angular_velocity", 0.0)
    
    my_planets = [p for p in planets if p.owner == player]
    enemy_planets = [p for p in planets if p.owner != -1 and p.owner != player]
    neutral_planets = [p for p in planets if p.owner == -1]
    
    all_targets = enemy_planets + neutral_planets
    if not my_planets or not all_targets:
        return []
    
    def is_threatened(planet):
        for f in fleets:
            if f.owner != player:
                dist = math.hypot(f.x - planet.x, f.y - planet.y)
                if dist < THREAT_DISTANCE:
                    return True
        return False
    
    moves = []
    assigned_targets = set()   
    
    for mine in my_planets:
        threatened = is_threatened(mine)
        reserve_ratio = BASE_RESERVE_RATIO + (0.2 if threatened else 0.0)
        reserve = max(MIN_ABSOLUTE_RESERVE, int(mine.ships * reserve_ratio))
        available = mine.ships - reserve
        if available < 1:
            continue
        
        best_target = None
        best_score = -1e9
        
        for target in all_targets:
            if target.id in assigned_targets:
                continue
            
            distance = math.hypot(target.x - mine.x, target.y - mine.y)
            if distance > MAX_ATTACK_DISTANCE or target.ships > MAX_TARGET_SHIPS:
                continue
            
            # ----- 预测目标未来位置（如果是轨道星球）-----
            avg_speed = 3.0
            travel_time = distance / avg_speed
            travel_time = max(1, int(travel_time))  
            
            init_target = next((p for p in initial_planets if p.id == target.id), None)
            if init_target and abs(angular_velocity) > 1e-6:
                init_dist = math.hypot(init_target.x - 50, init_target.y - 50)
                if init_dist < ROTATION_RADIUS_LIMIT:
                    cur_angle = math.atan2(target.y - 50, target.x - 50)
                    future_angle = cur_angle + angular_velocity * travel_time
                    future_x = 50 + init_dist * math.cos(future_angle)
                    future_y = 50 + init_dist * math.sin(future_angle)
                    pred_distance = math.hypot(future_x - mine.x, future_y - mine.y)
                    pred_angle = math.atan2(future_y - mine.y, future_x - mine.x)
                else:
                    pred_distance = distance
                    pred_angle = math.atan2(target.y - mine.y, target.x - mine.x)
            else:
                pred_distance = distance
                pred_angle = math.atan2(target.y - mine.y, target.x - mine.x)
            
            # ----- 考虑飞行期间目标的生产 -----
            production = target.production
            additional_ships = production * travel_time
            effective_defense = target.ships + additional_ships
            
            ships_needed = effective_defense + 1
            
            # ----- 检查我方是否有足够优势 -----
            if available < ships_needed * ADVANTAGE_FACTOR:
                continue
            
            # ----- 检查舰队路径是否会撞到太阳 -----
            spawn_x = mine.x + (mine.radius + 0.1) * math.cos(pred_angle)
            spawn_y = mine.y + (mine.radius + 0.1) * math.sin(pred_angle)
            target_x = future_x if (init_target and abs(angular_velocity)>1e-6) else target.x
            target_y = future_y if (init_target and abs(angular_velocity)>1e-6) else target.y
            if does_segment_hit_sun(spawn_x, spawn_y, target_x, target_y, sun_center, SUN_RADIUS):
                continue  
            
            # ----- 计算最终得分（优先级）-----
            enemy_bonus = 1000 if target.owner != -1 and target.owner != player else 0
            score = enemy_bonus + (target.production ** 2) / (pred_distance + 1) - target.ships * 0.5
            
            if score > best_score:
                best_score = score
                best_target = target
                # 保存最佳发射参数
                best_ships_needed = ships_needed
                best_angle = pred_angle
        
        if best_target is None:
            continue
        
        # 最终实际发射：使用精确计算的 needed 数量（但不超过可用）
        launch_ships = min(best_ships_needed, available)
        if launch_ships < 1:
            continue
        
        moves.append([mine.id, best_angle, launch_ships])
        assigned_targets.add(best_target.id)
    
    return moves

# ---------- 辅助函数：检测线段与太阳圆是否相交 ----------
def does_segment_hit_sun(x1, y1, x2, y2, sun_center, sun_radius):
    """检查从 (x1,y1) 到 (x2,y2) 的线段是否与太阳圆相交或穿过"""
    cx, cy = sun_center
    dx = x2 - x1
    dy = y2 - y1
    fx = x1 - cx
    fy = y1 - cy
    
    a = dx*dx + dy*dy
    if a == 0:
        return False  
    b = 2*(fx*dx + fy*dy)
    c = (fx*fx + fy*fy) - sun_radius*sun_radius
    discriminant = b*b - 4*a*c
    if discriminant < 0:
        return False
    sqrt_disc = math.sqrt(discriminant)
    t1 = (-b - sqrt_disc) / (2*a)
    t2 = (-b + sqrt_disc) / (2*a)
    if (0 <= t1 <= 1) or (0 <= t2 <= 1):
        return True
    return False