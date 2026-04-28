import random
from config import MUTATION_RATE, MUTATION_STD, GENOME_LEN


def random_genome():
    """Flat list of NN weights initialised in [-1, 1]."""
    return [random.uniform(-1.0, 1.0) for _ in range(GENOME_LEN)]


def mutate(genome):
    for i in range(len(genome)):
        if random.random() < MUTATION_RATE:
            genome[i] += random.gauss(0, MUTATION_STD)
            genome[i] = max(-5.0, min(5.0, genome[i]))


def crossover(g1, g2):
    """Uniform crossover over individual weights."""
    return [a if random.random() < 0.5 else b for a, b in zip(g1, g2)]
