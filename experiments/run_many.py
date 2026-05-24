from kaggle_environments import make
from pathlib import Path
from datetime import datetime
import csv
# 为方便记录，可以在每次实验后把experiment_summary.csv备注一下（如：1_experiment_summary）对应第几次的实验。再新建experiment_summary.csv

# =========================
# 1. 实验设置
# =========================

N_GAMES = 10   # 局数在这里修改
SEEDS = range(N_GAMES)   # 每局游戏的随机种子，在对比不同版本时保持一致，确保公平对比
OPPONENT = "random"

# 对应的 bot 路径，如果只对比某几个可以先把其他的comment掉
BOT_FILES = {
    "V1_baseline": "versions/v1_baseline.py",
    "V2_expansion": "versions/v2_expansion.py",
    #"V3_defense": "versions/v3_defense.py",
    #"Final": "versions/final.py",
}

RESULT_FILE = "results/experiment_summary.csv"


# =========================
# 2. 跑一局游戏
# =========================

def run_one_game(version_name, bot_file, seed):
    env = make("orbit_wars", configuration={"seed": seed}, debug=True)

    # 我们的 bot 放在 player 0，对手是 random
    env.run([bot_file, OPPONENT])

    final = env.steps[-1]

    my_state = final[0]
    opponent_state = final[1]

    my_reward = my_state.reward
    opponent_reward = opponent_state.reward

    my_status = my_state.status
    opponent_status = opponent_state.status

    # 简单判断是否赢：我方 reward 大于对手 reward
    if my_reward is None or opponent_reward is None:
        result = "unknown"
    elif my_reward > opponent_reward:
        result = "win"
    elif my_reward < opponent_reward:
        result = "loss"
    else:
        result = "draw"

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "version": version_name,
        "bot_file": bot_file,
        "opponent": OPPONENT,
        "seed": seed,
        "my_reward": my_reward,
        "opponent_reward": opponent_reward,
        "result": result,
        "my_status": my_status,
        "opponent_status": opponent_status,
    }


# =========================
# 3. 跑一个版本的多局游戏
# =========================

def run_bot_version(version_name, bot_file):
    rows = []

    print(f"\n===== Testing {version_name}: {bot_file} =====")

    for seed in SEEDS:
        try:
            row = run_one_game(version_name, bot_file, seed)
            rows.append(row)

            print(
                f"seed={seed} | "
                f"result={row['result']} | "
                f"my_reward={row['my_reward']} | "
                f"opponent_reward={row['opponent_reward']} | "
                f"status={row['my_status']}"
            )

        except Exception as e:
            row = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "version": version_name,
                "bot_file": bot_file,
                "opponent": OPPONENT,
                "seed": seed,
                "my_reward": None,
                "opponent_reward": None,
                "result": "error",
                "my_status": "error",
                "opponent_status": "error",
                "error_message": str(e),
            }
            rows.append(row)
            print(f"seed={seed} | ERROR: {e}")

    return rows


# =========================
# 4. 保存实验结果
# =========================

def save_results(rows, result_file):
    result_path = Path(result_file)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date",
        "version",
        "bot_file",
        "opponent",
        "seed",
        "my_reward",
        "opponent_reward",
        "result",
        "my_status",
        "opponent_status",
        "error_message",
    ]

    file_exists = result_path.exists()

    with open(result_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for row in rows:
            if "error_message" not in row:
                row["error_message"] = ""
            writer.writerow(row)

    print(f"\nResults saved to: {result_file}")


# =========================
# 5. 打印简单汇总
# =========================

def print_summary(rows):
    summary = {}

    for row in rows:
        version = row["version"]
        if version not in summary:
            summary[version] = {
                "games": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "errors": 0,
                "total_reward": 0,
                "valid_rewards": 0,
            }

        summary[version]["games"] += 1

        if row["result"] == "win":
            summary[version]["wins"] += 1
        elif row["result"] == "loss":
            summary[version]["losses"] += 1
        elif row["result"] == "draw":
            summary[version]["draws"] += 1
        elif row["result"] == "error":
            summary[version]["errors"] += 1

        if row["my_reward"] is not None:
            summary[version]["total_reward"] += row["my_reward"]
            summary[version]["valid_rewards"] += 1

    print("\n===== Summary =====")

    for version, s in summary.items():
        if s["valid_rewards"] > 0:
            avg_reward = s["total_reward"] / s["valid_rewards"]
        else:
            avg_reward = None

        print(
            f"{version}: "
            f"games={s['games']}, "
            f"wins={s['wins']}, "
            f"losses={s['losses']}, "
            f"draws={s['draws']}, "
            f"errors={s['errors']}, "
            f"avg_reward={avg_reward}"
        )


# =========================
# 6. 主程序
# =========================

def main():
    all_rows = []

    for version_name, bot_file in BOT_FILES.items():
        bot_path = Path(bot_file)

        if not bot_path.exists():
            print(f"\nSkip {version_name}: {bot_file} does not exist.")
            continue

        rows = run_bot_version(version_name, bot_file)
        all_rows.extend(rows)

    if all_rows:
        save_results(all_rows, RESULT_FILE)
        print_summary(all_rows)
    else:
        print("No bot files were found. Please check the versions/ folder.")


if __name__ == "__main__":
    main()