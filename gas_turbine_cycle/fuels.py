from scipy.integrate import quad
from abc import ABCMeta, abstractmethod


class Fuel(metaclass=ABCMeta):
    def __init__(self):
        self.T0 = 273

    @abstractmethod
    def get_c_p_real(self, T, **kwargs):
        pass

    def get_c_p_av(self, T, **kwargs):
        res = quad(lambda x: self.get_c_p_real(x, **kwargs), self.T0, T)[0] / (T - self.T0)
        return res

    def get_specific_enthalpy(self, T, **kwargs):
        return self.get_c_p_av(T, **kwargs) * (T - self.T0)


class NaturalGas(Fuel):
    def __init__(self):
        Fuel.__init__(self)
        self.rho0 = 0.73
        self.Q_n = 48.412e6

    def _get_gas_params(self, T, p):
        delta_b = 0.83 * self.rho0
        tau = T / (162.8 * (0.613 + delta_b))
        pi = 10.19 * p / (47.9 - delta_b)
        z = 1 - pi / tau * ((0.41 + 0.04 * pi) / tau**2 - 0.061)
        delta_c_p = 6 * pi / tau**3 * (0.41 + 0.02 * pi)
        return delta_c_p

    def get_c_p_real(self, T, **kwargs):
        if 'p' not in kwargs:
            assert False, 'p must be in kwargs'
        p = kwargs['p'] / 1e6
        delta_b = 0.83 * self.rho0
        R = 0.287 / delta_b
        exp = 2.811 + (0.3506 + 0.0078 * T) * delta_b
        c_p = R * (exp + self._get_gas_params(T, p))
        return c_p


