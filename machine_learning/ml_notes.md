# ML Attempt: Action Ranking

## Motivation

The current bot mainly relies on heuristic rules for decision making.

Early versions used relatively simple rules. For example, V2 introduced:

score = production / (distance + ships + 1)

The intuition is straightforward: planets with high production are attractive, while distant or heavily defended targets are less desirable.

As the project evolved, more components were gradually added, including defense reservation, threat detection, target prioritization, travel prediction, and environmental constraints.

These additions improved performance, but they also made the system harder to tune manually. Once multiple rules start interacting, adjusting one parameter can unexpectedly affect the behavior of others.

After reviewing the official Orbit Wars reinforcement learning tutorial, we considered introducing a lightweight ML component. The goal is not to replace the entire strategy, but to explore whether ML can help evaluate candidate actions.

---

## Current Decision Logic

At the current stage, the bot follows a heuristic-based pipeline:

Game State

↓

Apply strategy rules

↓

Evaluate candidate targets

↓

Select best action

The strategy evolved gradually over several versions.

V1:

Select the nearest available target.

V2:

Introduce a score function:

score = production / (distance + ships + 1)

to balance expected gain and attack cost.

V3:

Introduce defense reservation:

reserve = ships × reserve_ratio

to avoid overcommitting fleets.

The final heuristic version further adds:

- dynamic defense reservation
- nearby threat detection
- target prioritization
- travel-time production estimation
- orbital position prediction
- sun avoidance
- attack constraints
- simple target coordination

The system has gradually shifted from a single-rule strategy toward a combination of interacting heuristics.

---

## Proposed ML Idea

Instead of replacing the entire strategy, ML can be introduced as an additional ranking layer.

A possible workflow is:

Game State

↓

Generate candidate actions

↓

Extract features

↓

ML evaluates action quality

↓

Choose the highest-scoring action

Examples of candidate actions:

- attack an enemy planet
- expand to a neutral planet
- keep defending
- take no action

Under this design, heuristic rules still generate candidate actions, while ML only helps rank them.

This keeps the strategy relatively interpretable and avoids turning the bot into a complete black box.

---

## Candidate Features

Possible features can be grouped into local information, defense-related information, strategy-related information, environment-related information, and global information.

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
- is_threatened

Strategy-related:

- attack_advantage_ratio
- target_priority
- is_target_assigned

Environment-related:

- travel_time
- predicted_distance
- future_target_ships
- orbital_target_flag
- sun_path_blocked

Global information:

- my_total_ships
- enemy_total_ships
- my_planet_count
- enemy_planet_count
- round_id

Additional feature:

future_target_ships

= target_ships + production × travel_time

This approximates the number of ships a target may accumulate before our fleet arrives.

Some recent strategies already rely on future estimation rather than only using current observations.

---

## Data Collection

Current experiment outputs mainly record:

- seed
- reward
- win/loss result

These records are useful for comparison, but not sufficient for ML training.

If ML is introduced later, more detailed information should be stored.

For each game turn and decision step, we may record:

State:

- local features
- global features
- environmental features
- threat status
- predicted orbital information

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

The resulting structure becomes:

State → Action → Outcome

---

## Possible Training Pipeline

If enough data becomes available, a possible workflow could be:

Step 1:

Generate data from self-play experiments.

Step 2:

Build a dataset using:

Input:

State + Action

Output:

Action quality score

Examples:

- reward
- estimated winning probability

Because some strategies already depend on future estimation (such as orbital prediction and production growth during travel), feature preprocessing may also include future-state approximation.

Step 3:

Train lightweight models such as:

- Logistic Regression
- Random Forest
- XGBoost

Step 4:

Use model predictions to replace hand-designed scoring functions.

For example:

Current:

score = production / (distance + ships + 1)

Possible replacement:

score = model.predict(features)

---

## Current Limitation

The main limitation is still data availability.

The project currently does not generate enough samples for stable model training.

Another issue is that the strategy itself is still evolving. As new heuristics continue to be added, the feature set and decision process may also change.

Interpretability is another concern. Replacing heuristic strategies with a fully learned model too early may make the bot harder to understand and debug.

For now, ML is viewed as an experimental extension rather than a core component.

---

## Future Work

Future work may include:

- collecting larger self-play datasets
- testing lightweight ranking models
- trying reinforcement learning methods
- combining heuristic rules with ML approaches

Rather than replacing heuristic strategies completely, ML is expected to serve as a ranking layer on top of existing rules.

For now, the main focus remains building reliable and explainable strategies first.

The current goal is therefore not to build a full ML agent, but to prepare a framework for future experiments.
