import numpy as np


class GasDynamicFunctions:

    @staticmethod
    def a_cr(T_stag, k, R):
        return np.sqrt(2 * k * R * T_stag / (k + 1))

    @staticmethod
    def tau_lam(lam, k):
        """ГДФ температруы через приведенную скорость"""
        return 1 - (k - 1) / (k + 1) * lam**2

    @staticmethod
    def pi_lam(lam, k):
        """ГДФ давления через приведенную скорость"""
        return (1 - (k - 1) / (k + 1) * lam**2) ** (k / (k - 1))

    @staticmethod
    def eps_lam(lam, k):
        """ГДФ плотности через приведенную скорость"""
        return (1 - (k - 1) / (k + 1) * lam**2) ** (1 / (k - 1))

    @staticmethod
    def tau_M(M, k):
        """ГДФ температуры через число Маха"""
        return 1 + (k - 1) / 2 * M ** 2

    @staticmethod
    def pi_M(M, k):
        """ГДФ давления через число Маха"""
        return (1 + (k - 1) / 2 * M ** 2) ** (k / (k - 1))

    @staticmethod
    def lam(k, **kwargs):
        if 'tau' in kwargs:
            return np.sqrt((1 - kwargs['tau']) * (k + 1) / (k - 1))
        if 'pi' in kwargs:
            return np.sqrt((k + 1) / (k - 1) * (1 - kwargs['pi']**((k - 1) / k)))


class GasDynamicsParameters:
    def __init__(self, **kwargs):

        def cond(a1: str, a2: str, a3: str, a4: str, a5: str) -> bool:
            return (a1 in kwargs) and (a2 in kwargs) and (a3 in kwargs) and (a4 in kwargs) and (a5 in kwargs)

        if cond('k', 'R', 'T', 'p', 'c'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T = kwargs['T']
            self.p = kwargs['p']
            self.c = kwargs['c']
            self.c_p = self.k * self.R / (self.k - 1)
            self.T_stag = self.T + self.c ** 2 / (2 * self.c_p)
            self.lam = self.c / GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.p_stag = self.p / GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T', 'p_stag', 'c'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T = kwargs['T']
            self.p_stag = kwargs['p_stag']
            self.c = kwargs['c']
            self.c_p = self.k * self.R / (self.k - 1)
            self.T_stag = self.T + self.c ** 2 / (2 * self.c_p)
            self.lam = self.c / GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.p = self.p_stag * GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T_stag', 'p_stag', 'c'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T_stag = kwargs['T_stag']
            self.p_stag = kwargs['p_stag']
            self.c = kwargs['c']
            self.c_p = self.k * self.R / (self.k - 1)
            self.T = self.T_stag - self.c ** 2 / (2 * self.c_p)
            self.lam = self.c / GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.p = self.p_stag * GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T_stag', 'p', 'c'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T_stag = kwargs['T_stag']
            self.p = kwargs['p']
            self.c = kwargs['c']
            self.c_p = self.k * self.R / (self.k - 1)
            self.T = self.T_stag - self.c ** 2 / (2 * self.c_p)
            self.lam = self.c / GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.p_stag = self.p / GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T', 'p', 'T_stag'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T = kwargs['T']
            self.p = kwargs['p']
            self.T_stag = kwargs['T_stag']
            self.c_p = self.k * self.R / (self.k - 1)
            self.lam = GasDynamicFunctions.lam(self.k, tau=self.T / self.T_stag)
            self.c = self.lam * GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.p_stag = self.p / GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T', 'p_stag', 'T_stag'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T = kwargs['T']
            self.p_stag = kwargs['p_stag']
            self.T_stag = kwargs['T_stag']
            self.c_p = self.k * self.R / (self.k - 1)
            self.lam = GasDynamicFunctions.lam(self.k, tau=self.T / self.T_stag)
            self.c = self.lam * GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.p = self.p_stag * GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T', 'p', 'p_stag'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T = kwargs['T']
            self.p = kwargs['p']
            self.p_stag = kwargs['p_stag']
            self.c_p = self.k * self.R / (self.k - 1)
            self.lam = GasDynamicFunctions.lam(self.k, pi=self.p / self.p_stag)
            self.T_stag = self.T / GasDynamicFunctions.tau_lam(self.lam, self.k)
            self.c = self.lam * GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T_stag', 'p', 'p_stag'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T_stag = kwargs['T_stag']
            self.p = kwargs['p']
            self.p_stag = kwargs['p_stag']
            self.c_p = self.k * self.R / (self.k - 1)
            self.lam = GasDynamicFunctions.lam(self.k, pi=self.p / self.p_stag)
            self.c = self.lam * GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.T = self.T_stag * GasDynamicFunctions.tau_lam(self.lam, self.k)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)

        if cond('k', 'R', 'T_stag', 'p', 'lam'):
            self.k = kwargs['k']
            self.R = kwargs['R']
            self.T_stag = kwargs['T_stag']
            self.p = kwargs['p']
            self.lam = kwargs['lam']
            self.c_p = self.k * self.R / (self.k - 1)
            self.p_stag = self.p / GasDynamicFunctions.pi_lam(self.lam, self.k)
            self.T = self.T_stag * GasDynamicFunctions.tau_lam(self.lam, self.k)
            self.c = self.lam * GasDynamicFunctions.a_cr(self.T_stag, self.k, self.R)
            self.rho = self.p / (self.R * self.T)
            self.rho_stag = self.p_stag / (self.R * self.T_stag)
