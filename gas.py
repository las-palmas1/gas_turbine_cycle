from abc import ABCMeta, abstractproperty, abstractstaticmethod, abstractmethod


class IdealGas(metaclass=ABCMeta):
    def __init__(self):
        self._R = None
        self._T = None
        self._T1 = None
        self._T2 = None
        self._c_p = None
        self._c_p_av = None
        self._c_p_av_int = None
        self._k = None
        self._k_av = None
        self._k_av_int = None

    def rho_func(self, T, p):
        return p / (self._R * T)

    def T_func(self, p, rho):
        return p / (self._R * rho)

    def p_func(self, T, rho):
        return self._R * rho * T

    def _k_func(self, c_p):
        return c_p / (c_p - self._R)

    def _c_p_func(self, k):
        return k * self._R / (k - 1)

    @property
    def R(self):
        return self._R

    @property
    def k(self):
        return self._k

    @property
    def k_av(self):
        return self._k_av

    @property
    def k_av_int(self):
        return self._k_av_int

    @property
    def c_p(self):
        return self._c_p

    @property
    def c_p_av(self):
        return self._c_p_av

    @property
    def c_p_av_int(self):
        return self._c_p_av_int

    @abstractmethod
    def _T_get(self):
        pass

    @abstractmethod
    def _T_set(self, value):
        pass

    T = abstractproperty(_T_get, _T_set)

    @abstractmethod
    def _T1_get(self):
        pass

    @abstractmethod
    def _T1_set(self, value):
        pass

    T1 = abstractproperty(_T1_get, _T1_set)

    @abstractmethod
    def _T2_get(self):
        pass

    @abstractmethod
    def _T2_set(self, value):
        pass

    T2 = abstractproperty(_T2_get, _T2_set)

    @abstractmethod
    def _c_p_real_func(self, T, **kwargs):
        pass

    @abstractmethod
    def _c_p_av_func(self, T, **kwargs):
        pass

    @abstractmethod
    def _c_p_av_int_func(self, T1, T2, **kwargs):
        pass


class Air(IdealGas):
    def __init__(self):
        IdealGas.__init__(self)
        self._R = 287.4
        self._T = 288
        self._T1 = 288
        self._T2 = 400
        self._c_p = self._c_p_real_func(self._T)
        self._c_p_av = self._c_p_av_func(self._T)
        self._c_p_av_int = self._c_p_av_int_func(self._T1, self._T2)
        self._k = self._k_func(self._c_p)
        self._k_av = self._k_func(self._c_p_av)
        self._k_av_int = self._k_func(self._c_p_av_int)

    def _T_get(self):
        return self._T

    def _T_set(self, value):
        self._T = value
        self._c_p = self._c_p_real_func(value)
        self._k = self._c_p / (self._c_p - self._R)
        self._c_p_av = self._c_p_av_func(value)
        self._k_av = self._c_p_av / (self._c_p_av - self._R)

    T = property(_T_get, _T_set)

    def _T1_get(self):
        return self._T1

    def _T1_set(self, value):
        self._T1 = value
        self._c_p_av_int = self._c_p_av_int_func(value, self._T2)
        self._k_av_int = self._c_p_av_int / (self._c_p_av_int - self._R)

    T1 = property(_T1_get, _T1_set)

    def _T2_get(self):
        return self._T2

    def _T2_set(self, value):
        self._T2 = value
        self._c_p_av_int = self._c_p_av_int_func(self._T1, value)
        self._k_av_int = self._c_p_av_int / (self._c_p_av_int - self._R)

    T2 = property(_T2_get, _T2_set)

    def _c_p_real_func(self, T, **kwargs):
        """Истинная удельная теплоемкость воздуха"""
        exp1 = 1e3 * (0.2407 + 0.0193 * (2.5 * 1e-3 * T - 0.875) +
                      2 * 1e-3 * (2.5 * 1e-5 * T ** 2 - 0.0275 * T + 6.5625)) * 4.187
        exp2 = 1e3 * (0.26 + 0.032 * (1.176 * 1e-3 * T - 0.88235) -
                      0.374 * 1e-2 * (5.5556 * 1e-6 * T ** 2 - 1.3056 * 1e-2 * T + 6.67)) * 4.187
        return exp1 * (T < 750) + exp2 * (T >= 750)

    def _c_p_av_func(self, T, **kwargs):
        """Средняя удельная теплоемкость воздуха"""
        exp1 = 4.187e3 * (1.2e-5 * (T - 70) + 0.236)
        exp2 = 4.187e3 * (2.2e-5 * (T + 450) + 0.218)
        return exp1 * (T < 700) + exp2 * (T >= 700)

    def _c_p_av_int_func(self, T1, T2, **kwargs):
        """Средняя теплоемкость воздуха в интервале температур"""
        T0 = 273
        return (self._c_p_av_func(T2) * (T2 - T0) - self._c_p_av_func(T1) * (T1 - T0)) / (T2 - T1)


class KeroseneCombustionProducts(IdealGas):
    def __init__(self):
        IdealGas.__init__(self)
        self._R = 287.4
        self._alpha = 1
        self._T = 288
        self._T1 = 288
        self._T2 = 400
        self._c_p = self._c_p_real_func(self._T, alpha=self._alpha)
        self._c_p_av = self._c_p_av_func(self._T, alpha=self._alpha)
        self._c_p_av_int = self._c_p_av_int_func(self._T1, self._T2, alpha=self._alpha)
        self._k = self._k_func(self._c_p)
        self._k_av = self._k_func(self._c_p_av)
        self._k_av_int = self._k_func(self._c_p_av_int)

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value

    def _T_get(self):
        return self._T

    def _T_set(self, value):
        self._T = value
        self._c_p = self._c_p_real_func(value, alpha=self._alpha)
        self._k = self._c_p / (self._c_p - self._R)
        self._c_p_av = self._c_p_av_func(value, alpha=self._alpha)
        self._k_av = self._c_p_av / (self._c_p_av - self._R)

    T = property(_T_get, _T_set)

    def _T1_get(self):
        return self._T1

    def _T1_set(self, value):
        self._T1 = value
        self._c_p_av_int = self._c_p_av_int_func(value, self._T2, alpha=self._alpha)
        self._k_av_int = self._c_p_av_int / (self._c_p_av_int - self._R)

    T1 = property(_T1_get, _T1_set)

    def _T2_get(self):
        return self._T2

    def _T2_set(self, value):
        self._T2 = value
        self._c_p_av_int = self._c_p_av_int_func(self._T1, value, alpha=self._alpha)
        self._k_av_int = self._c_p_av_int / (self._c_p_av_int - self._R)

    T2 = property(_T2_get, _T2_set)

    def _c_p_real_func(self, T, **kwargs):
        """Истинная удельная теплоемкость продуктов сгорания керосина"""
        alpha = kwargs['alpha']
        term11 = 0.0174 / alpha + 0.2407
        term12 = (0.0093 / alpha + 0.0193) * (2.5 * 1e-3 * T - 0.875)
        term13 = (2e-3 - 1.056e-3 / (alpha - 0.2)) * (2.5e-5 * T ** 2 - 0.0275 * T + 6.5625)
        exp1 = 4.187e3 * (term11 + term12 + term13)
        term21 = 0.0267 / alpha + 0.26
        term22 = (0.0133 / alpha + 0.032) * (1.176e-3 * T - 0.88235)
        term23 = (0.374e-2 + 0.94e-2 / (alpha ** 2 + 10)) * (5.5556e-6 * T ** 2 - 1.3056e-2 * T + 6.67)
        exp2 = 4.187e3 * (term21 + term22 - term23)
        return exp1 * (T < 750) + exp2 * (T >= 750)

    def _c_p_av_func(self, T, **kwargs):
        """Средняя удельная теплоемкость продуктов сгорания керосина"""
        alpha = kwargs['alpha']
        exp1 = ((2.25 + 1.2 * alpha) * (T - 70) / (alpha * 1e5) + 0.236) * 4.187e3
        exp2 = ((1.25 + 2.2 * alpha) * (T + 450) / (alpha * 1e5) + 0.218) * 4.187e3
        return exp1 * (T < 700) + exp2 * (T >= 700)

    def _c_p_av_int_func(self, T1, T2, **kwargs):
        """Средняя удельная теплоемкость продуктов сгорания керосина в интервале температур"""
        alpha = kwargs['alpha']
        T0 = 273
        return (self._c_p_av_func(T2, alpha=alpha) * (T2 - T0) -
                self._c_p_av_func(T1, alpha=alpha) * (T1 - T0)) / (T2 - T1)

