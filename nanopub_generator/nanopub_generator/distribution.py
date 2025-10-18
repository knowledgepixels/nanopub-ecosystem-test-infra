from random import Random


class ParetoDist:
    """https://en.wikipedia.org/wiki/Pareto_distribution#Generating_bounded_Pareto_random_variables"""

    def __init__(self, rng: Random, minimum: int, maximum: int, alpha: float = 0.5):
        self.rng = rng
        self.alpha = alpha
        l = minimum + 1  # lower bound
        h = maximum + 1  # upper bound
        self.la = l**self.alpha
        self.ha = h**self.alpha
        self.exp = -1 / self.alpha
        self.laha = self.la * self.ha

    def sample(self):
        """Sample an item from the data based on a power-law distribution."""
        u = self.rng.random()
        x1 = -(u * self.ha - u * self.la - self.ha) / self.laha
        x2 = x1**self.exp
        return int(round(x2 - 1, 0))


class ParetoDistList(ParetoDist):
    """https://en.wikipedia.org/wiki/Pareto_distribution#Generating_bounded_Pareto_random_variables"""

    def __init__(self, data: list, rng: Random, alpha: float = 0.5):
        super().__init__(rng, 0, len(data) - 1, alpha)
        self.data = data

    def sample_item(self):
        """Sample an item from the data based on a power-law distribution."""
        return self.data[self.sample()]
