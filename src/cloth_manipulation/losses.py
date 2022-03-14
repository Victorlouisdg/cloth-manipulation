import numpy as np


def distances(positions0, positions1):
    return np.linalg.norm(positions0 - positions1, axis=1)


def mean_distance(positions0, positions1):
    distances_ = distances(positions0, positions1)
    return distances_.mean(axis=0)


def mean_squared_distance(positions0, positions1):
    distances_ = distances(positions0, positions1)
    sq_distances = distances_ ** 2
    return sq_distances.mean(axis=0)


def root_mean_squared_distance(positions0, positions1):
    return np.sqrt(mean_squared_distance(positions0, positions1))
