# ga.py

from config import POP_SIZE, ELITE_COUNT, PARENT_POOL
from genome import random_genome, mutate, crossover
from simulator import simulate_genome


def evaluate_population(population, track):
    scored = []
    for genome in population:
        fitness, _ = simulate_genome(genome, track)
        scored.append((fitness, genome))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def next_generation(scored, genome_len):
    new_pop = []

    # Elites
    for i in range(ELITE_COUNT):
        new_pop.append(scored[i][1][:])

    # Parents pool
    parents = [g for (_, g) in scored[:PARENT_POOL]]

    # Fill rest
    while len(new_pop) < POP_SIZE:
        import random
        p1 = random.choice(parents)
        p2 = random.choice(parents)
        child = crossover(p1, p2)
        mutate(child)
        new_pop.append(child)

    # Ensure correct length
    for i in range(len(new_pop)):
        g = new_pop[i]
        if len(g) < genome_len:
            g = g[:] + [random_genome(1)[0] for _ in range(genome_len - len(g))]
        elif len(g) > genome_len:
            g = g[:genome_len]
        new_pop[i] = g

    return new_pop


# small helper so we don't import random_genome directly above
from genome import random_genome
