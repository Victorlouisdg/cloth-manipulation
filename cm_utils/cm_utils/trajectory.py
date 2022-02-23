from cm_utils.time_parametrization import Linear


class Trajectory:
    def __init__(self, path, time_parametrization=Linear()):
        self.path = path
        self.time_parametrization = time_parametrization

    def pose(self, time_completion):
        path_completion = self.time_parametrization.map(time_completion)
        return self.path.pose(path_completion)
