# ML Attempt: Action Ranking

## Motivation

Current versions of our bot (V1/V2/V3) mainly rely on heuristic rules for decision making.

For example, V2 uses:

score = production / (distance + ships + 1)

The basic idea is straightforward: prefer planets with high production while avoiding targets that are far away or heavily defended.

This approach works reasonably well and is easy to understand. However, hand-crafted rules also have limitations. As the game becomes more complex, manually designed formulas may miss interactions between multiple factors.

After reading the official Orbit Wars reinforcement learning tutorial, we considered a lightweight machine learning extension. The goal is not to let ML control the entire bot, but to see whether it can help evaluate candidate actions.

---

## Current Decision Logic

At the current stage, the bot follows a simple pipeline:

Game State

↓

Calculate heuristic score

↓

Choose the best target

Examples:

V1:

Select the nearest target.

V2:

Use a manually designed score function:

score = production / (distance + ships + 1)

V3:

Add defensive considerations by reserving part of the fleet.

Compared with V1, later versions already consider more strategic information, but the scoring function is still manually designed.

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

Possible features can be divided into local information and global information.

Local information:

- distance
- source_ships
- source_production
- target_ships
- target_production
- reserve_after_send
- target_owner

Global information:

- my_total_ships
- enemy_total_ships
- my_planet_count
- enemy_planet_count
- round_id

We may also include:

future_target_ships

= target_ships + distance × production

The purpose of this feature is to roughly estimate how many ships the target planet may accumulate before our fleet arrives.

This is important because current versions mainly consider the target's current state, while ignoring growth during travel time.

---

## Data Collection

At the moment, experiment outputs mainly record:

- seed
- reward
- win/loss result

This information is useful for comparison, but not enough for training a model.

If ML is added later, more detailed records will be needed.

For each decision step, we may record:

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

Reward or winning probability

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

---

## Future Work

Future work may focus on:

- collecting larger self-play datasets
- testing lightweight ranking models
- trying reinforcement learning approaches
- combining heuristic rules with ML methods

For now, the project mainly focuses on building reliable and explainable strategies first.
