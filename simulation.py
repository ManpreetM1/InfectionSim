import sys
import traceback
import pygame
import random
import math
import pandas as pd
from datetime import datetime

# ---------------------------
# Simulation Parameters
# ---------------------------
WIDTH, HEIGHT = 800, 600
N_AGENTS = 120

RADIUS = 4                   # agent size
INFECTION_RADIUS = 12        # distance for infection
INFECTION_PROB = 0.15        # probability of infection on contact
RECOVERY_TIME = 600          # frames until infected recovers

# Colors
SUS_COLOR = (50, 150, 255)
INF_COLOR = (255, 80, 80)
REC_COLOR = (80, 200, 120)
BG_COLOR = (20, 20, 20)

# ---------------------------
# Agent class
# ---------------------------
class Agent:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(-1.2, 1.2)

        self.state = "S"  # S, I, or R
        self.time_infected = 0

    def update_position(self):
        self.x += self.vx
        self.y += self.vy

        # bounce off walls
        if self.x <= 0 or self.x >= WIDTH:
            self.vx *= -1
        if self.y <= 0 or self.y >= HEIGHT:
            self.vy *= -1

    def update_state(self):
        if self.state == "I":
            self.time_infected += 1
            if self.time_infected >= RECOVERY_TIME:
                self.state = "R"

    def try_infect(self, others):
        if self.state != "I":
            return

        for agent in others:
            if agent.state == "S":
                dist = math.hypot(self.x - agent.x, self.y - agent.y)
                if dist < INFECTION_RADIUS and random.random() < INFECTION_PROB:
                    agent.state = "I"

    def draw(self, surface):
        color = SUS_COLOR if self.state == "S" else INF_COLOR if self.state == "I" else REC_COLOR
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), RADIUS)

# ---------------------------
# Main Simulation
# ---------------------------
def main():
    pygame.init()
    print("Creating Window...")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    agents = [Agent() for _ in range(N_AGENTS)]
    # Seed one infected
    agents[0].state = "I"

    # Data logging
    data = []

    running = True
    frame = 0

    while running:
        frame += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG_COLOR)

        # Update states and positions
        for agent in agents:
            agent.update_position()
            agent.update_state()

        # Infection spread
        for agent in agents:
            agent.try_infect(agents)

        # Draw everything
        for agent in agents:
            agent.draw(screen)

        pygame.display.flip()
        clock.tick(60)

        # Log SIR counts
        if frame % 10 == 0:
            S = sum(a.state == "S" for a in agents)
            I = sum(a.state == "I" for a in agents)
            R = sum(a.state == "R" for a in agents)
            data.append({"frame": frame, "S": S, "I": I, "R": R})

    if __name__ == "__main__":
        try:
            main()
        except Exception:
            traceback.print_exc()
            input("\nERROR OCCURRED. Press Enter to exit...")

    pygame.quit()

    # Save data to Pandas DataFrame
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
