# ga.py

import random
from config import POP_SIZE, ELITE_COUNT, PARENT_POOL
from genome import random_genome, mutate, crossover
from simulator import simulate_genome


def evaluate_population(population, track):
    scored = [(simulate_genome(genome, track)[0], genome) for genome in population]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def next_generation(scored):
    new_pop = [scored[i][1][:] for i in range(ELITE_COUNT)]

    parents = [g for (_, g) in scored[:PARENT_POOL]]

    while len(new_pop) < POP_SIZE:
        p1 = random.choice(parents)
        p2 = random.choice(parents)
        child = crossover(p1, p2)
        mutate(child)
        new_pop.append(child)

    return new_pop
