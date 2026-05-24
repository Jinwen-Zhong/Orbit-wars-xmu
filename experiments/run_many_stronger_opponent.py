from kaggle_environments import make
from pathlib import Path
from datetime import date
import csv


# ============================================================
# 实验配置区：只需要改这里
# ============================================================

# 将原来的 random 对手升级为更强的 opponent_strong
OPPONENT = "versions/opponent_strong.py"

# 要测试的 bot：分别测试 V1 和 V2 对抗强对手的表现
BOT_FILES = {
    "V1_baseline": "versions/v1_baseline.py",
    "V2_expansion": "versions/v2_expansion.py",
}

START_SEED = 0
NUM_SEEDS = 10

OUTPUT_NAME = "experiment_summary_strong_opponent.csv"


# ============================================================
# 下面一般不用改
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT_ROOT / "results"


def resolve_agent(agent_text):
    """
    如果是 random, 就直接返回 random。
    如果是文件路径，就转换为绝对路径。
    """
    if agent_text == "random":
        return "random"

    path = Path(agent_text)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Agent file not found: {path}")

    return str(path.resolve())


def run_one_game(bot_name, bot_file, opponent, seed):
    """
    运行一局游戏。
    bot_file 作为 player0，opponent 作为 player1。
    """
    bot_agent = resolve_agent(bot_file)
    opponent_agent = resolve_agent(opponent)

    env = make("orbit_wars", configuration={"seed": seed}, debug=True)

    env.run([
        bot_agent,
        opponent_agent,
    ])

    final = env.steps[-1]

    my_reward = final[0].reward
    opponent_reward = final[1].reward
    my_status = final[0].status
    opponent_status = final[1].status

    if my_reward > opponent_reward:
        result = "win"
    elif my_reward < opponent_reward:
        result = "loss"
    else:
        result = "draw"

    return {
        "date": date.today().strftime("%Y/%m/%d"),
        "bot_name": bot_name,
        "bot_file": bot_file,
        "opponent": opponent,
        "seed": seed,
        "result": result,
        "my_reward": my_reward,
        "opponent_reward": opponent_reward,
        "my_status": my_status,
        "opponent_status": opponent_status,
    }


def save_records(records, output_path):
    fieldnames = [
        "date",
        "bot_name",
        "bot_file",
        "opponent",
        "seed",
        "result",
        "my_reward",
        "opponent_reward",
        "my_status",
        "opponent_status",
    ]

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def summarize(records):
    print()
    print("===== Summary =====")

    for bot_name in BOT_FILES.keys():
        bot_records = [r for r in records if r["bot_name"] == bot_name]

        games = len(bot_records)
        wins = sum(1 for r in bot_records if r["result"] == "win")
        losses = sum(1 for r in bot_records if r["result"] == "loss")
        draws = sum(1 for r in bot_records if r["result"] == "draw")
        errors = sum(1 for r in bot_records if r["my_status"] != "DONE")
        avg_reward = sum(r["my_reward"] for r in bot_records) / games if games > 0 else 0

        print(
            f"{bot_name}: "
            f"games={games}, "
            f"wins={wins}, "
            f"losses={losses}, "
            f"draws={draws}, "
            f"errors={errors}, "
            f"avg_reward={avg_reward:.3f}"
        )


def main():
    records = []

    print(f"Opponent: {OPPONENT}")
    print(f"Seeds: {START_SEED} to {START_SEED + NUM_SEEDS - 1}")

    for bot_name, bot_file in BOT_FILES.items():
        print()
        print(f"===== Testing {bot_name}: {bot_file} =====")

        for seed in range(START_SEED, START_SEED + NUM_SEEDS):
            record = run_one_game(bot_name, bot_file, OPPONENT, seed)
            records.append(record)

            print(
                f"seed={seed} | "
                f"result={record['result']} | "
                f"my_reward={record['my_reward']} | "
                f"opponent_reward={record['opponent_reward']} | "
                f"status={record['my_status']}"
            )

    output_path = RESULT_DIR / OUTPUT_NAME
    save_records(records, output_path)

    print()
    print(f"Results saved to: {output_path.relative_to(PROJECT_ROOT)}")

    summarize(records)


if __name__ == "__main__":
    main()