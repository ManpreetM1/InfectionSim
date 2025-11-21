import random
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# -------------------------
# Simulation Parameters
# -------------------------
N_AGENTS = 150
WIDTH, HEIGHT = 800, 600          # Used only for movement, no pygame needed
INFECTION_RADIUS = 10
INFECTION_PROB = 0.12
RECOVERY_TIME = 50                # steps until recovery
STEPS = 300                       # total number of frames

# -------------------------
# Agent setup
# -------------------------
agents = pd.DataFrame({
    "x": [random.uniform(0, WIDTH) for _ in range(N_AGENTS)],
    "y": [random.uniform(0, HEIGHT) for _ in range(N_AGENTS)],
    "vx": [random.uniform(-1.2, 1.2) for _ in range(N_AGENTS)],
    "vy": [random.uniform(-1.2, 1.2) for _ in range(N_AGENTS)],
    "state": ["S"] * N_AGENTS,
    "time_infected": [0] * N_AGENTS,
})

# Seed initial infection
agents.loc[0, "state"] = "I"

sir_log = []   # will store S, I, R values over time

# -------------------------
# Simulation step
# -------------------------
def update_agents():
    global agents

    # Move agents
    agents["x"] += agents["vx"]
    agents["y"] += agents["vy"]

    # Bounce off walls
    agents.loc[(agents["x"] < 0) | (agents["x"] > WIDTH), "vx"] *= -1
    agents.loc[(agents["y"] < 0) | (agents["y"] > HEIGHT), "vy"] *= -1

    # Infection spread
    infected = agents[agents["state"] == "I"]

    for idx, inf in infected.iterrows():
        for jdx, sus in agents[agents["state"] == "S"].iterrows():
            dist = math.hypot(inf["x"] - sus["x"], inf["y"] - sus["y"])
            if dist < INFECTION_RADIUS and random.random() < INFECTION_PROB:
                agents.at[jdx, "state"] = "I"

    # Update infection timers→recovery
    agents.loc[agents["state"] == "I", "time_infected"] += 1
    agents.loc[agents["time_infected"] >= RECOVERY_TIME, "state"] = "R"

# -------------------------
# Matplotlib Bar Graph
# -------------------------
fig, ax = plt.subplots()
bars = ax.bar(["S", "I", "R"], [0, 0, 0], color=["#3399ff", "#ff4444", "#44cc88"])
ax.set_ylim(0, N_AGENTS)
ax.set_title("SIR Simulation (Pandas + Matplotlib)")
ax.set_ylabel("Population Count")

def animate(frame):
    update_agents()

    # Count categories
    S = (agents["state"] == "S").sum()
    I = (agents["state"] == "I").sum()
    R = (agents["state"] == "R").sum()

    sir_log.append([frame, S, I, R])

    # Update bars
    bars[0].set_height(S)
    bars[1].set_height(I)
    bars[2].set_height(R)

    ax.set_title(f"SIR Simulation — Step {frame}")

    return bars

# Run animation
anim = FuncAnimation(fig, animate, frames=STEPS, interval=60, repeat=False)
plt.show()

# Save SIR results
df_sir = pd.DataFrame(sir_log, columns=["step", "S", "I", "R"])
df_sir.to_csv("sir_results_pandas.csv", index=False)
print(df_sir.head())
print("Simulation complete. CSV saved.")
