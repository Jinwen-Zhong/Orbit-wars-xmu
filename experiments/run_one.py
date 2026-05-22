from kaggle_environments import make


def main():
    env = make("orbit_wars", configuration={"seed": 42}, debug=True)

    env.run(["main.py", "random"])

    final = env.steps[-1]

    print("Game finished.")
    for i, state in enumerate(final):
        print(f"Player {i}: reward={state.reward}, status={state.status}")


if __name__ == "__main__":
    main()