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
INFECTION_RADIUS = 50
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
agents.loc[5, "state"] = "I"

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

x=[]
S_vals=[]
I_vals=[]
R_vals=[]

line_S, = ax.plot([], [], color="#1100ff", marker='o', label="S")
line_I, = ax.plot([], [], color="#ff0000", marker='x', label="I")
line_R, = ax.plot([], [], color="#00ff0d", marker='o', label="R")

#bars = ax.bar(["S", "I", "R"], [0, 0, 0], color=["#3399ff", "#ff4444", "#44cc88"])
ax.set_xlim(0, STEPS)
ax.set_ylim(0, N_AGENTS)
ax.set_title("SIR Simulation (Pandas + Matplotlib)")
ax.set_ylabel("Population Count")
ax.legend()

def animate(frame):
    update_agents()

    # Count categories
    S = (agents["state"] == "S").sum()
    I = (agents["state"] == "I").sum()
    R = (agents["state"] == "R").sum()

    sir_log.append([frame, S, I, R])

    # Update plots
    x.append(frame)
    S_vals.append(S)
    I_vals.append(I)
    R_vals.append(R)

    line_S.set_xdata(x)
    line_I.set_xdata(x)
    line_R.set_xdata(x)

    line_S.set_ydata(S_vals)
    line_I.set_ydata(I_vals)
    line_R.set_ydata(R_vals)


    ax.set_title(f"SIR Simulation — Step {frame}")

    return line_S, line_I, line_R

# Run animation
anim = FuncAnimation(fig, animate, frames=range(0, STEPS, 10), interval=560, repeat=False)
plt.show()

# Save SIR results
df_sir = pd.DataFrame(sir_log, columns=["step", "S", "I", "R"])
df_sir.to_csv("sir_results_pandas.csv", index=False)
print(df_sir.head())
print("Simulation complete. CSV saved.")
