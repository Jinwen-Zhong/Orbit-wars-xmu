# ML Attempt: Action Ranking

## Inspiration

Our design is inspired by the official Orbit Wars reinforcement learning tutorial.

Instead of directly controlling the whole bot, the tutorial simplifies decision making into candidate action selection.

We adopt a similar idea while keeping the strategy interpretable.

---

## Current Pipeline

Current versions (V1/V2/V3) use heuristic rules:

Game State
↓
Score Function
↓
Select Best Target

For example:
score = production / (distance + ships + 1)

---

## Proposed ML Extension

Future versions may replace hand-crafted scoring with a lightweight action ranking model.

Pipeline:

Game State
↓
Generate Candidate Actions
↓
ML scores candidates
↓
Select best action

Examples:

- attack enemy planet
- expand to neutral planet
- defend current planet
- no-op

---

## Candidate Features

Local features:

- distance
- source_ships
- target_ships
- target_production
- reserve_after_send
- target_owner

Global features:

- my_total_ships
- enemy_total_ships
- my_planet_count
- enemy_planet_count
- round_id

Additional feature:

future_target_ships
=target_ships + distance × production

---

## Current Limitation

Current experiments only store:
- seed
- reward
- win/loss

Training ML models requires:

State
Action
Outcome

The dataset is currently insufficient.

---

## Future Work

Future versions may record:

State → Action → Reward

through:

- V1 vs V2
- V2 vs V3
- Strong Opponent vs Final

This dataset may support:

- Random Forest
- XGBoost
- Reinforcement Learning

for future experiments.
