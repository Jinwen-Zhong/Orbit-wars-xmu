from kaggle_environments import make
from pathlib import Path
from datetime import date
import csv


# ============================================================
# 只改这里：实验配置区
# ============================================================

BOT_A = "versions/v1_baseline.py"
BOT_B = "versions/v2_expansion.py"

START_SEED = 0
NUM_SEEDS = 10

# True 表示双方交换 player 顺序：
# 例如 V1 vs V2 跑一遍，V2 vs V1 再跑一遍
SWAP_ORDER = True

OUTPUT_NAME = "head_to_head_v1_vs_v2.csv"

# ============================================================
# 下面一般不用改
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT_ROOT / "experiments" / "results"


def resolve_bot_path(path_text):
    path = Path(path_text)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Bot file not found: {path}")

    return path.resolve()


def bot_name(path):
    return path.stem


def run_one_game(player0_path, player1_path, seed, bot_a_name, bot_b_name, order_note):
    env = make("orbit_wars", configuration={"seed": seed}, debug=True)

    env.run([
        str(player0_path),
        str(player1_path),
    ])

    final = env.steps[-1]

    reward0 = final[0].reward
    reward1 = final[1].reward
    status0 = final[0].status
    status1 = final[1].status

    player0_name = bot_name(player0_path)
    player1_name = bot_name(player1_path)

    if reward0 > reward1:
        winner_player = "player0"
        winner_bot = player0_name
    elif reward1 > reward0:
        winner_player = "player1"
        winner_bot = player1_name
    else:
        winner_player = "tie"
        winner_bot = "tie"

    return {
        "date": date.today().strftime("%Y/%m/%d"),
        "seed": seed,
        "bot_a": bot_a_name,
        "bot_b": bot_b_name,
        "player0": player0_name,
        "player1": player1_name,
        "player0_file": str(player0_path.relative_to(PROJECT_ROOT)),
        "player1_file": str(player1_path.relative_to(PROJECT_ROOT)),
        "reward0": reward0,
        "reward1": reward1,
        "status0": status0,
        "status1": status1,
        "winner_player": winner_player,
        "winner_bot": winner_bot,
        "order_note": order_note,
    }


def save_records(records, output_path):
    fieldnames = [
        "date",
        "seed",
        "bot_a",
        "bot_b",
        "player0",
        "player1",
        "player0_file",
        "player1_file",
        "reward0",
        "reward1",
        "status0",
        "status1",
        "winner_player",
        "winner_bot",
        "order_note",
    ]

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def summarize(records, bot_a_name, bot_b_name):
    bot_a_wins = 0
    bot_b_wins = 0
    ties = 0

    for r in records:
        if r["winner_bot"] == bot_a_name:
            bot_a_wins += 1
        elif r["winner_bot"] == bot_b_name:
            bot_b_wins += 1
        else:
            ties += 1

    total = len(records)

    print()
    print("Experiment finished.")
    print(f"Bot A: {bot_a_name}")
    print(f"Bot B: {bot_b_name}")
    print(f"Total games: {total}")
    print(f"{bot_a_name} wins: {bot_a_wins}")
    print(f"{bot_b_name} wins: {bot_b_wins}")
    print(f"Ties: {ties}")

    if total > 0:
        print(f"{bot_a_name} win rate: {bot_a_wins / total:.2%}")
        print(f"{bot_b_name} win rate: {bot_b_wins / total:.2%}")


def main():
    bot_a_path = resolve_bot_path(BOT_A)
    bot_b_path = resolve_bot_path(BOT_B)

    bot_a_name = bot_name(bot_a_path)
    bot_b_name = bot_name(bot_b_path)

    records = []

    for seed in range(START_SEED, START_SEED + NUM_SEEDS):
        records.append(
            run_one_game(
                bot_a_path,
                bot_b_path,
                seed,
                bot_a_name,
                bot_b_name,
                f"{bot_a_name} as player0, {bot_b_name} as player1",
            )
        )

        if SWAP_ORDER:
            records.append(
                run_one_game(
                    bot_b_path,
                    bot_a_path,
                    seed,
                    bot_a_name,
                    bot_b_name,
                    f"{bot_b_name} as player0, {bot_a_name} as player1",
                )
            )

    output_path = RESULT_DIR / OUTPUT_NAME

    save_records(records, output_path)
    summarize(records, bot_a_name, bot_b_name)

    print(f"Results saved to: {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()