
import random
from config import MUTATION_RATE, MUTATION_STD


def random_gene():
    # steer, throttle in [-1, 1]
    return (random.uniform(-1, 1), random.uniform(-1, 1))


def random_genome(length):
    return [random_gene() for _ in range(length)]


def mutate(genome):
    for i in range(len(genome)):
        if random.random() < MUTATION_RATE:
            s, t = genome[i]
            s += random.gauss(0, MUTATION_STD)
            t += random.gauss(0, MUTATION_STD)
            s = max(-1, min(1, s))
            t = max(-1, min(1, t))
            genome[i] = (s, t)


def crossover(g1, g2):
    # uniform crossover
    assert len(g1) == len(g2)
    child = []
    for a, b in zip(g1, g2):
        child.append(a if random.random() < 0.5 else b)
    return child
