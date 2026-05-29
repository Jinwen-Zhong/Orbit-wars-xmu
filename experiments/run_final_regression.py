from __future__ import annotations

import csv
import importlib.util
import sys
from datetime import date
from pathlib import Path

from kaggle_environments import make


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT_ROOT / "results"
OUTPUT_NAME = "8_experiment_summary_final_improved_200.csv"
NUM_SEEDS = 100

MATCHUPS = [
    ("final_improved_vs_v3_100", "final_improved", "versions/final.py", "v3_defense", "versions/v3_defense.py"),
    (
        "final_improved_vs_harder_100",
        "final_improved",
        "versions/final.py",
        "harder_opponent",
        "versions/harder_opponent.py",
    ),
]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(path)
    return path.resolve()


def load_agent(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.agent


def run_one(experiment: str, player0_name: str, player0_path: Path, player1_name: str, player1_path: Path, seed: int):
    player0_agent = load_agent(player0_path, f"{player0_name}_{seed}_p0")
    player1_agent = load_agent(player1_path, f"{player1_name}_{seed}_p1")
    env = make("orbit_wars", configuration={"seed": seed}, debug=True)
    env.run([player0_agent, player1_agent])

    final = env.steps[-1]
    reward0 = final[0].reward
    reward1 = final[1].reward
    status0 = final[0].status
    status1 = final[1].status

    if reward0 > reward1:
        winner = player0_name
    elif reward1 > reward0:
        winner = player1_name
    else:
        winner = "draw"

    return {
        "date": date.today().strftime("%Y/%m/%d"),
        "experiment": experiment,
        "player0_name": player0_name,
        "player0_file": str(player0_path.relative_to(PROJECT_ROOT)),
        "player1_name": player1_name,
        "player1_file": str(player1_path.relative_to(PROJECT_ROOT)),
        "seed": seed,
        "winner": winner,
        "reward0": reward0,
        "reward1": reward1,
        "status0": status0,
        "status1": status1,
    }


def summarize(records):
    by_experiment = {}
    for record in records:
        bucket = by_experiment.setdefault(record["experiment"], {"games": 0, "wins0": 0, "wins1": 0, "draws": 0})
        bucket["games"] += 1
        if record["winner"] == record["player0_name"]:
            bucket["wins0"] += 1
        elif record["winner"] == record["player1_name"]:
            bucket["wins1"] += 1
        else:
            bucket["draws"] += 1
    return by_experiment


def main():
    records = []
    for experiment, player0_name, player0_file, player1_name, player1_file in MATCHUPS:
        player0_path = resolve(player0_file)
        player1_path = resolve(player1_file)
        for seed in range(NUM_SEEDS):
            records.append(run_one(experiment, player0_name, player0_path, player1_name, player1_path, seed))

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULT_DIR / OUTPUT_NAME
    fieldnames = [
        "date",
        "experiment",
        "player0_name",
        "player0_file",
        "player1_name",
        "player1_file",
        "seed",
        "winner",
        "reward0",
        "reward1",
        "status0",
        "status1",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    for experiment, stats in summarize(records).items():
        print(
            f"{experiment}: games={stats['games']}, "
            f"player0_wins={stats['wins0']}, player1_wins={stats['wins1']}, draws={stats['draws']}"
        )
    print(f"saved={output_path}")


if __name__ == "__main__":
    main()
