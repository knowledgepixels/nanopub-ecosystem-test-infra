from random import Random

class ParetoDist:
    """https://en.wikipedia.org/wiki/Pareto_distribution#Generating_bounded_Pareto_random_variables"""
    def __init__(self, data: list, rng: Random):
        self.data = data
        self.rng = rng
        self.alpha = 0.5
        l = 1 # lower bound
        h = len(data) + 1 # upper bound
        self.la = l ** self.alpha
        self.ha = h ** self.alpha
        self.exp = (-1 / self.alpha)
        self.laha = self.la * self.ha

    def sample(self):
        """Sample an item from the data based on a power-law distribution."""
        u = self.rng.random()
        x1 = -(u * self.ha - u * self.la - self.ha) / self.laha
        x2 = x1 ** self.exp
        x3 = int(round(x2 - 1, 0))
        return self.data[x3]
