import random
import math
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Simulation Parameters
N_AGENTS = 525                      # Number of simulated agents (Based off Hay Lakes, Alberta in 2021)
MAXWIDTH, MAXHEIGHT = 770, 770      # Maximum dimensions of simulation area (Based off Hay Lakes, Alberta in 2021)
BASE_INFECTION_RADIUS = 2           # Base radius where infection is possible between susceptible and infected agent (Quereshi et al. 2020)
BASE_INFECTION_PROB = 0.011         # Base infection probability when in contact (Ferreti et al. 2024)
RECOVERY_TIME = 288                 # Hours until recovery (12 days) (Nichita et al. 2022)
STEPS = 728                         # Total number of time steps simulated in hours, around 30 days with 8 extra days for the range function
SIM_INTERVAL = 8                    # The interval at which the simulation generates values, currently set at 8 hours
INITIAL_INFECTION_PROB = 0.025      # Inital probability for an agent to be randomly infected (Wang et al. 2023)


# Variables based on simulation parameters
width, height = MAXWIDTH, MAXHEIGHT             # Current Dimensions of simulation area, initalized to maxwidth and maxheight
infection_prob = BASE_INFECTION_PROB            # Current infection probabillty, initalized to base infection probability
infection_radius = BASE_INFECTION_RADIUS        # Current infection radius, inialized to base infection radius


# Intervention variables (Change these to change the simulation)
vaccination = True
isolation = True

vaccine_infection_prob = 0.595 * BASE_INFECTION_PROB          # Infection probability under vaccine scenario, approximately 90% reduction (simpleified since vaccine rollout takes time and is not consistent across population) (Oordt-Speetz et al. 2023)

# Infection probability in shopping centers, approximately 32% increase, it's capped at 1 since greater than 1 probability can't exist
shopping_infection_prob = min(infection_prob * 1.32, 1) 
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

def create_agents(n):
    global agents
    # Creates the agents using pandas dataframes
    agents = pd.DataFrame({
        "x": [random.uniform(0, width) for _ in range(N_AGENTS)],
        "y": [random.uniform(0, height) for _ in range(N_AGENTS)],
        "vx": [random.uniform(-1.2, 1.2) for _ in range(N_AGENTS)],
        "vy": [random.uniform(-1.2, 1.2) for _ in range(N_AGENTS)],
        "state": ["S"] * N_AGENTS,
        "time_infected": [0] * N_AGENTS,
    })

# Simulates the working period by forcing the agents into a smaller boundary (set to 1/4th here but can be changed)
def work_period():
    global width
    global height
    width = MAXWIDTH/4
    height = MAXHEIGHT/4
    agents.loc[(agents["x"] > width), "x"] = random.uniform(0, width)
    agents.loc[(agents["y"] > height), "y"] = random.uniform(0, height)

# Creates a few hardcoded shopping centers, for consistency
def generate_shops():
    shop1 = ShoppingCentre(300, 200, [100, 100])
    shop2 = ShoppingCentre(200, 100, [200, 200])
    shop3 = ShoppingCentre(100, 100, [400, 400])
    shopping_centres.append(shop1)
    shopping_centres.append(shop2)
    shopping_centres.append(shop3)



# Simulation starts here
sir_log = []                 # will store S, I, R values over time

steps_left = SIM_INTERVAL    # Stores the current time steps left before the next work periods starts, initalized at SIM_INTERVAL so it can scale with it
step_subtraction = (SIM_INTERVAL/3) # Stores the amount that the steps_left variable will be subtracted every loop, can be scaled for more or less work periods

generate_shops()

if(vaccination): 
    infection_prob = vaccine_infection_prob

create_agents(N_AGENTS)

# Creates a mask from which a subset of agents will be selected
initial_infection_agents = agents.index.to_series().sample(frac = INITIAL_INFECTION_PROB, replace = False)
infection_mask = agents.index.isin(initial_infection_agents)

# Seed initial infection in those chosen agents from the previous mask created
agents.loc[infection_mask, "state"] = "I"

def update_agents():
    global agents
    global steps_left
    global width, height

    #print("max x: " + str(width) + ", max y:" + str(height))
    #print(shopping_centres)

    # Every n=3 Time steps using whichever interval we've specified runs the work period, where the boundary for agents is constrained
    if steps_left <= 0:
        # print(current_step)
        work_period()
        steps_left = SIM_INTERVAL
    else:
        width, height = MAXWIDTH, MAXHEIGHT

    # Move agents
    agents["x"] += agents["vx"]
    agents["y"] += agents["vy"]

    # Bounce off if agent hits boundary of the simulation
    agents.loc[(agents["x"] < 0) | (agents["x"] > width), "vx"] *= -1
    agents.loc[(agents["y"] < 0) | (agents["y"] > height), "vy"] *= -1

    # Infection spread
    infected = agents[agents["state"] == "I"]
    susceptible = agents[agents["state"] == "S"]

    for idx, inf in infected.iterrows():
        for jdx, sus in susceptible.iterrows():
            dist = math.hypot(inf["x"] - sus["x"], inf["y"] - sus["y"])
            if dist < infection_radius:
                # print(f"infection radius: {infection_radius}")
                for s in shopping_centres:
                    if(s.is_in(inf["x"], inf["y"]) and s.is_in(sus["x"], sus["y"])):
                        infect_risk = shopping_infection_prob
                        # print(f"shopping infect risk: {infect_risk}")
                        # print(f"{inf['x']}, {inf['y']} and {sus['x']}, {sus['y']} infected at shopping centre:{s.x}, {s.y} ")
                    else:
                        infect_risk = infection_prob
                        if random.random() < infect_risk:
                            agents.at[jdx, "state"] = "I"
                            # print("Infection at:" + str(agents.at[jdx, "x"]) + ", " + str(agents.at[jdx, "y"]))
                            # print("Infected at:" + str(sus["x"]) + ", " + str(sus["y"]))

    # Update infection timer
    agents.loc[agents["state"] == "I", "time_infected"] += SIM_INTERVAL

    # 9% of infected population is quarantined divided by 24 since our simulation is in hours, considered recovered for our purposes under isolation scenario(Aleta et al. 2020)
    if(isolation):                              
        infected_agents = agents.loc[(agents["state"] == "I")]  
        quarantined_agents = infected_agents.sample(frac = 0.00375, replace = False)   
        quarantine_mask = agents.index.isin(quarantined_agents.index)
        agents.loc[quarantine_mask, "state"] = "R"
        print(len(quarantined_agents))
    
    # A random sampling of infected agents
    infected_eligible_agents = agents.loc[(agents["state"] == "I") & (agents["time_infected"] >= RECOVERY_TIME)]
    recovery_agents = infected_eligible_agents.sample(frac = 0.1, replace = False)  # 10% of agents past recovery time will be recovered every day to simulate differences in immunity

    #print(len(infected_agents))
    #print(len(recovery_agents))

    # This will randomly select 10 infected agents to recover, this is to simulate the differences in recovery for individuals over time
    recovery_mask = agents.index.isin(recovery_agents.index)
    agents.loc[recovery_mask, "state"] = "R"
    #agents.loc[agents["time_infected"] >= RECOVERY_TIME, "state"] = "R"

    # Updates time steps left unitl work period, set to subtract by a third of the set SIM_INTERVAL 
    # but can be scaled to change number of work periods in simulation
    steps_left -= step_subtraction

# Bar graph animation setup
fig, ax = plt.subplots(figsize=(14, 10))

x=[]
S_vals=[]
I_vals=[]
R_vals=[]

line_S, = ax.plot([], [], color="#1100ff", marker='d', label="S")
line_I, = ax.plot([], [], color="#ff0000", marker='d', label="I")
line_R, = ax.plot([], [], color="#00ff0d", marker='d', label="R")

#bars = ax.bar(["S", "I", "R"], [0, 0, 0], color=["#3399ff", "#ff4444", "#44cc88"])
ax.set_xlim(0, STEPS)
ax.set_ylim(0, N_AGENTS)
ax.set_title("SIR Simulation (Pandas + Matplotlib)")
ax.set_ylabel("Population Count")
ax.set_xlabel("Hours")
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


    ax.set_title(f"SIR Simulation — 30 Days (720 Hours)")

    return line_S, line_I, line_R

# Run animation
anim = FuncAnimation(fig, animate, frames=range(0, STEPS, SIM_INTERVAL), interval=100, repeat=False)
plt.show()

# Save SIR results
df_sir = pd.DataFrame(sir_log, columns=["step", "S", "I", "R"])
df_sir.to_csv("sir_results_pandas.csv", index=False)
print(df_sir.head())
print("Simulation completed, CSV file saved in local directory.")
