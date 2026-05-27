# ML Attempt: Action Ranking

## Motivation

Current versions of our bot mainly rely on heuristic rules for decision making.

For example, V2 uses:

score = production / (distance + ships + 1)

The intuition is simple: prefer planets with high production while avoiding distant or heavily defended targets.

As the project evolved, more manually designed components were introduced, including defense reservation, attack constraints, and target prioritization.

As more rules are added, interactions between them become increasingly difficult to tune manually.

This motivates exploring a lightweight ML extension that learns action quality from data instead of relying entirely on manually adjusted thresholds.

After reading the official Orbit Wars reinforcement learning tutorial, we considered a lightweight machine learning extension. The goal is not to let ML control the entire bot, but to see whether it can help evaluate candidate actions.

---

## Current Decision Logic

At the current stage, the bot follows a heuristic-based decision pipeline:

Game State

↓

Calculate heuristic score

↓

Choose the best target

Examples:

V1:

Select the nearest target.

V2:

Introduce a score function:

score = production / (distance + ships + 1)

to balance potential gain and attack cost.

V3:

Add a reserve mechanism:

reserve = ships × reserve_ratio

to avoid sending all fleets and improve defense.

The stronger opponent version further introduces:

- target prioritization
- attack distance constraints
- advantage checks
- simple target coordination

These changes make decisions less dependent on a single rule and more dependent on multiple interacting conditions.

---

## Proposed ML Idea

Instead of replacing the whole strategy, ML can be introduced as an additional ranking component.

The overall process could look like:

Game State

↓

Generate several candidate actions

↓

Extract features

↓

ML model evaluates each action

↓

Choose the highest-scoring action

Examples of candidate actions:

- attack an enemy planet
- expand to a neutral planet
- keep defending
- take no action

Under this design, heuristic rules still generate actions, while ML only helps decide which action looks more promising.

This keeps the strategy relatively interpretable and avoids turning the bot into a complete black box.

---

## Candidate Features

Possible features can be grouped into local information, defense-related information, strategy-related information, and global information.

Local information:

- distance
- source_ships
- source_production
- target_ships
- target_production
- target_owner

Defense-related:

- reserve_ratio
- reserve_after_send
- available_ships

Strategy-related:

- attack_advantage_ratio
- target_priority
- target_already_assigned

Global information:

- my_total_ships
- enemy_total_ships
- my_planet_count
- enemy_planet_count
- round_id

Additional feature:

future_target_ships

= target_ships + distance × production

This approximates target growth during fleet travel time.

---

## Data Collection

At the moment, experiment outputs mainly record:

- seed
- reward
- win/loss result

This information is useful for comparison, but not enough for training a model.

If ML is added later, more detailed records will be needed.

For each game turn and decision step, we may record:

State:

- local features
- global features

Action:

- target_id
- ships_sent
- action_type

Outcome:

- reward
- final result

Data can be generated automatically through self-play experiments such as:

- V1 vs V2
- V2 vs V3
- Strong Opponent vs Final

The overall structure becomes:

State → Action → Outcome

---

## Possible Training Pipeline

If enough data becomes available, the training process could be:

Step 1:

Generate data from self-play experiments.

Step 2:

Build a dataset using:

Input:

State + Action

Output:

Action quality score
(e.g., reward or estimated winning probability)

Step 3:

Train a lightweight model, for example:

- Logistic Regression
- Random Forest
- XGBoost

Step 4:

Use model predictions to replace hand-designed scores.

For example:

Current:

score = production / (distance + ships + 1)

Potential replacement:

score = model.predict(features)

---

## Current Limitation

The main issue is data size.

At the current stage, the project does not produce enough training samples for a stable machine learning model.

Another concern is interpretability. Replacing heuristic strategies with a fully learned policy too early may make the bot harder to understand and debug.

For this reason, ML is currently viewed as an experimental extension rather than a core component.

In addition, the current versions are still evolving, which means the feature set and decision logic may continue to change.

---

## Future Work

Future work may focus on:

- collecting larger self-play datasets
- testing lightweight ranking models
- trying reinforcement learning approaches
- combining heuristic rules with ML methods

Rather than replacing heuristic strategies completely, ML is expected to serve as a ranking layer on top of existing rules.

For now, the project mainly focuses on building reliable and explainable strategies first.

The current goal is therefore not to build a full ML agent, but to prepare a framework for future experiments.
