import random
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# -------------------------
# Simulation Parameters
# -------------------------
N_AGENTS = 250                  # Number of simulated agents
MAXWIDTH,MAXHEIGHT = 800, 600   # Maximum dimensions of simulation area
INFECTION_RADIUS = 20           # Radius where infection is possible between susceptible and infected agent
INFECTION_PROB = 0.9            # Infection probability when in contact, based on the 3 least dense populated states (Alaska, Wyoming, Montana)
RECOVERY_TIME = 150             # Time steps until recovery
STEPS = 300                     # Total number of time steps simulated
SIM_INTERVAL = 5                # The interval at which the simulation generates values
INITIAL_INFECTION_PROB = 0.025  # Inital probability for an agent to be randomly infected

# Variables based on simulation parameters
width, height = MAXWIDTH, MAXHEIGHT             # Current Dimensions of simulation area, initalized to maxwidth and maxheight
vaccine_infection_prob = 0.1 * INFECTION_PROB   # Infection probability under vaccine scenario, approximately 90% reduction
# Infection probability in shopping centers, approximately 32% increase, it's capped at 1 since greater than 1 probability can't exist
shopping_infection_prob = max(INFECTION_PROB + (0.32 * INFECTION_PROB), 1) 
shopping_centres = []


class ShoppingCentre:
    def __init__(self, x=random.uniform(1, width), y=random.uniform(1,height), top_left=[random.uniform(0, width/2), random.uniform(0,height/2)]):
        self.x = x
        self.y = y
        self.top_left = top_left
        #self.area = (self.x - self.top_left[0]), (self.y - self.top_left[1]) 

    def is_in(self, x, y):
        # print(f"{self.top_left[0]} < {x} < {self.x + self.top_left[0]} and {self.top_left[1]} < {y} < {self.y + self.top_left[1]}")
        return(self.top_left[0] < x < self.x + self.top_left[0] and self.top_left[1] < y < self.y + self.top_left[1])
    
    def __repr__(self):
        return f"X:{self.x}, Y:{self.y}, TL: {self.top_left}"

# -------------------------
# Agent setup
# -------------------------
agents = pd.DataFrame({
    "x": [random.uniform(0, width) for _ in range(N_AGENTS)],
    "y": [random.uniform(0, height) for _ in range(N_AGENTS)],
    "vx": [random.uniform(-1.2, 1.2) for _ in range(N_AGENTS)],
    "vy": [random.uniform(-1.2, 1.2) for _ in range(N_AGENTS)],
    "state": ["S"] * N_AGENTS,
    "time_infected": [0] * N_AGENTS,
})

initial_infection_agents = agents.index.to_series().sample(frac = INITIAL_INFECTION_PROB, replace = False)
infection_mask = agents.index.isin(initial_infection_agents)

# Seed initial infection
agents.loc[infection_mask, "state"] = "I"


sir_log = []   # will store S, I, R values over time

steps_left = SIM_INTERVAL    # Stores the current time steps left before the next work periods starts, initalized at SIM_INTERVAL so it can scale with it
step_subtraction = (SIM_INTERVAL/3) # Stores the amount that the steps_left variable will be subtracted every loop, can be scaled for more or less work periods

def work_period():
    global width
    global height
    width = MAXWIDTH/2
    height = MAXHEIGHT/2
    agents.loc[(agents["x"] > width), "x"] = random.uniform(0, width)
    agents.loc[(agents["y"] > height), "y"] = random.uniform(0, height)

def generate_shops():
    shop1 = ShoppingCentre(100, 200, [100, 100])
    shop2 = ShoppingCentre(200, 100, [200, 200])
    shopping_centres.append(shop1)
    shopping_centres.append(shop2)

# -------------------------
# Simulation step
# -------------------------

generate_shops()

def update_agents():
    global agents
    global steps_left
    global width, height
    print("max x: " + str(width) + ", max y:" + str(height))
    print(shopping_centres)
    if steps_left <= 0:
        # print(current_step)
        work_period()
        steps_left = SIM_INTERVAL
    else:
        width, height = MAXWIDTH, MAXHEIGHT

    # Move agents
    agents["x"] += agents["vx"]
    agents["y"] += agents["vy"]

    # Bounce off walls
    agents.loc[(agents["x"] < 0) | (agents["x"] > width), "vx"] *= -1
    agents.loc[(agents["y"] < 0) | (agents["y"] > height), "vy"] *= -1

    # Infection spread
    infected = agents[agents["state"] == "I"]

    for idx, inf in infected.iterrows():
        for jdx, sus in agents[agents["state"] == "S"].iterrows():
            dist = math.hypot(inf["x"] - sus["x"], inf["y"] - sus["y"])
            if dist < INFECTION_RADIUS:
                for s in shopping_centres:
                    if(s.is_in(inf["x"], inf["y"]) and s.is_in(sus["x"], sus["y"])):
                        infect_risk = shopping_infection_prob
                    else:
                        infect_risk = INFECTION_PROB
                        if random.random() < infect_risk:
                            agents.at[jdx, "state"] = "I"
                            # print("Infection at:" + str(agents.at[jdx, "x"]) + ", " + str(agents.at[jdx, "y"]))
                            # print("Infected at:" + str(sus["x"]) + ", " + str(sus["y"]))

    # Update infection timers→recovery
    agents.loc[agents["state"] == "I", "time_infected"] += SIM_INTERVAL
    agents.loc[agents["time_infected"] >= RECOVERY_TIME, "state"] = "R"

    # Updates time steps left unitl work period, set to subtract by a third of the set SIM_INTERVAL 
    # but can be scaled to change number of work periods in simulation
    steps_left -= step_subtraction

# -------------------------
# Matplotlib Bar Graph
# -------------------------
fig, ax = plt.subplots()

x=[]
S_vals=[]
I_vals=[]
R_vals=[]

line_S, = ax.plot([], [], color="#1100ff", marker='h', label="S")
line_I, = ax.plot([], [], color="#ff0000", marker='x', label="I")
line_R, = ax.plot([], [], color="#00ff0d", marker='d', label="R")

#bars = ax.bar(["S", "I", "R"], [0, 0, 0], color=["#3399ff", "#ff4444", "#44cc88"])
ax.set_xlim(0, STEPS)
ax.set_ylim(0, N_AGENTS)
ax.set_title("SIR Simulation (Pandas + Matplotlib)")
ax.set_ylabel("Population Count")
ax.set_xlabel("Time Steps")
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
anim = FuncAnimation(fig, animate, frames=range(0, STEPS, SIM_INTERVAL), interval=100, repeat=False)
plt.show()

# Save SIR results
df_sir = pd.DataFrame(sir_log, columns=["step", "S", "I", "R"])
df_sir.to_csv("sir_results_pandas.csv", index=False)
print(df_sir.head())
print("Simulation complete. CSV saved.")
