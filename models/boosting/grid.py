from functools import lru_cache

import numpy as np

# def get_grid_idx(x, y):
#     return (x // grid_cell_size) - (grid_min // grid_cell_size), (y // grid_cell_size) - (
#             grid_min // grid_cell_size),

class Grid:
    def __init__(self, grid_min, grid_max, grid_cell_size, cell_distance, cell_angle):
        self.grid_min = grid_min
        self.grid_max = grid_max
        self.grid_cell_size = grid_cell_size
        self.cell_distance = cell_distance
        self.cell_angle = cell_angle

        self.grid_size = (grid_max - grid_min) // grid_cell_size
        self.num_cells = self.grid_size ** 2

        self.ijs = np.array([[i, j] for i in range(self.grid_size) for j in range(self.grid_size)])
        self.xy_points = np.array([list(self.grid_to_xy(i, j)) for i, j in self.ijs])

    def grid_to_xy(self, i, j):
        return (i + (self.grid_min // self.grid_cell_size)) * self.grid_cell_size - self.grid_cell_size / 2.0, \
               (j + (self.grid_min // self.grid_cell_size)) * self.grid_cell_size - self.grid_cell_size / 2.0,

    @lru_cache(maxsize=10000)
    def get_grid_points_for_cell(self, cell_x, cell_y, cell_azimuth):
        xy_cell = np.array([cell_x, cell_y]).reshape(-1, 2).repeat(self.num_cells, axis=0)
        distances = np.linalg.norm(xy_cell - self.xy_points, axis=1)

        azimuth_vectors = np.array([np.cos((360 - cell_azimuth + 90) / 180 * np.pi), \
                                    np.sin((360 - cell_azimuth + 90) / 180 * np.pi)]) \
            .reshape(-1, 2).repeat(self.num_cells, axis=0)

        azimuth_vectors = azimuth_vectors / np.linalg.norm(azimuth_vectors[0, :])

        direction_vectors = self.xy_points - xy_cell

        direction_vectors = direction_vectors / np.linalg.norm(direction_vectors, axis=1).reshape(
            direction_vectors.shape[0], -1)

        angles = np.arccos(np.einsum('ij,ij->i', direction_vectors, azimuth_vectors)) / np.pi * 180

        result = []
        for i, (angle_b, dist_b) in enumerate(zip(angles, distances)):
            if dist_b <= self.cell_distance and angle_b <= self.cell_angle:
                result.append(i)
        return result

    def new_grid(self):
        return np.zeros(shape=(self.grid_size, self.grid_size))
