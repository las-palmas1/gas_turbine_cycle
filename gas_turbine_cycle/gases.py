from abc import ABCMeta, abstractproperty, abstractstaticmethod, abstractmethod
from scipy.interpolate import interp2d
import numpy as np


class IdealGas(metaclass=ABCMeta):
    def __init__(self):
        self._R = None
        self._T = None
        self._T1 = None
        self._T2 = None
        self._l0 = None
        self._Q_n = None
        self._c_p = None
        self._c_p_av = None
        self._c_p_av_int = None
        self._k = None
        self._k_av = None
        self._k_av_int = None
        self._alpha = 1

    @property
    def l0(self):
        """Теоретически необходимая масса воздуха"""
        return self._l0

    @property
    def Q_n(self):
        """Низшая теплота сгорания топлива"""
        return self._Q_n

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value

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
    def mu(self, T):
        """Динамическая вязкость при заданной температуре."""
        pass

    @abstractmethod
    def lam(self, T):
        """Теплопроводность при заданной температуре."""
        pass

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

    def mu(self, T):
        return 17.6e-6 * (T / 273) ** 0.68

    def lam(self, T):
        return 0.0244 * (T / 273) ** 0.82

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
        self._Q_n = 43e6
        self._l0 = 14.61
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
        self._c_p = self._c_p_real_func(self._T, alpha=value)
        self._k = self._c_p / (self._c_p - self._R)
        self._c_p_av = self._c_p_av_func(self._T, alpha=value)
        self._k_av = self._c_p_av / (self._c_p_av - self._R)
        self._c_p_av_int = self._c_p_av_int_func(self._T1, self._T2, alpha=value)
        self._k_av_int = self._c_p_av_int / (self._c_p_av_int - self._R)

    def _T_get(self):
        return self._T

    def _T_set(self, value):
        self._T = value
        self._c_p = self._c_p_real_func(value, alpha=self._alpha)
        self._k = self._c_p / (self._c_p - self._R)
        self._c_p_av = self._c_p_av_func(value, alpha=self._alpha)
        self._k_av = self._c_p_av / (self._c_p_av - self._R)

    T = property(_T_get, _T_set)

    def mu(self, T):
        return 17.6e-6 * (T / 273) ** 0.68

    def lam(self, T):
        return 0.0244 * (T / 273) ** 0.82

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


class NaturalGasCombustionProducts(IdealGas):
    def __init__(self):
        IdealGas.__init__(self)
        self._R = 300.67
        self._alpha = 1
        self._T = 288
        self._T1 = 288
        self._T2 = 400
        self._Q_n = 48.412e6
        self._l0 = 16.683

        self._c_p_real_1 = [1.0999, 1.0532, 1.0370, 1.0288, 1.0239, 1.0205, 1.0182, 1.0164, 1.0150, 1.0138]
        self._c_p_real_2 = [1.1201, 1.0665, 1.0480, 1.0386, 1.0329, 1.0291, 1.0263, 1.0243, 1.0227, 1.0214]
        self._c_p_real_3 = [1.1462, 1.0873, 1.0669, 1.0566, 1.0503, 1.0462, 1.0431, 1.0409, 1.0391, 1.0377]
        self._c_p_real_4 = [1.1760, 1.1126, 1.0907, 1.0795, 1.0728, 1.0683, 1.0651, 1.0626, 1.0607, 1.0592]
        self._c_p_real_5 = [1.2075, 1.1400, 1.1167, 1.1048, 1.0976, 1.0928, 1.0894, 1.0868, 1.0848, 1.0831]
        self._c_p_real_6 = [1.2394, 1.1678, 1.1431, 1.1305, 1.1229, 1.1178, 1.1141, 1.1114, 1.1092, 1.1075]
        self._c_p_real_7 = [1.2704, 1.1948, 1.1686, 1.1553, 1.1473, 1.1419, 1.1380, 1.1351, 1.1329, 1.1310]
        self._c_p_real_8 = [1.2998, 1.2201, 1.1924, 1.1784, 1.1699, 1.1643, 1.1602, 1.1571, 1.1547, 1.1528]
        self._c_p_real_9 = [1.3272, 1.2432, 1.2142, 1.1994, 1.1905, 1.1845, 1.1802, 1.1770, 1.1745, 1.1725]
        self._c_p_real_10 = [1.3521, 1.2641, 1.2336, 1.2181, 1.2087, 1.2025, 1.1980, 1.1946, 1.1920, 1.1899]
        self._c_p_real_11 = [1.3745, 1.2826, 1.2507, 1.2345, 1.2248, 1.2182, 1.2135, 1.2100, 1.2073, 1.2051]
        self._c_p_real_12 = [1.3945, 1.2989, 1.2658, 1.2490, 1.2388, 1.2320, 1.2271, 1.2235, 1.2206, 1.2183]
        self._c_p_real_13 = [1.4123, 1.3133, 1.2790, 1.2617, 1.2511, 1.2441, 1.2390, 1.2352, 1.2323, 1.2299]
        self._c_p_real_14 = [1.4281, 1.3261, 1.2908, 1.2729, 1.2621, 1.2548, 1.2496, 1.2457, 1.2426, 1.2402]
        self._c_p_real_15 = [1.4423, 1.3376, 1.3014, 1.2830, 1.2719, 1.2644, 1.2591, 1.2551, 1.2519, 1.2494]
        self._c_p_real_16 = [1.4550, 1.3481, 1.3110, 1.2922, 1.2808, 1.2732, 1.2677, 1.2636, 1.2604, 1.2579]
        self._c_p_real_17 = [1.4667, 1.3576, 1.3198, 1.3007, 1.2891, 1.2813, 1.2757, 1.2716, 1.2683, 1.2657]
        self._c_p_real_18 = [1.4774, 1.3664, 1.3280, 1.3085, 1.2967, 1.2888, 1.2831, 1.2789, 1.2756, 1.2729]
        self._c_p_real_19 = [1.4871, 1.3745, 1.3354, 1.3156, 1.3037, 1.2956, 1.2899, 1.2856, 1.2822, 1.2795]
        self._c_p_real_20 = [1.4957, 1.3816, 1.3420, 1.3220, 1.3099, 1.3017, 1.2959, 1.2915, 1.2881, 1.2854]
        self._c_p_real_21 = [1.5028, 1.3875, 1.3476, 1.3273, 1.3151, 1.3069, 1.3010, 1.2966, 1.2931, 1.2904]

        self._c_p_real_arr = np.array([self._c_p_real_1, self._c_p_real_2, self._c_p_real_3, self._c_p_real_4,
                                       self._c_p_real_5, self._c_p_real_6, self._c_p_real_7, self._c_p_real_8,
                                       self._c_p_real_9, self._c_p_real_10, self._c_p_real_11, self._c_p_real_12,
                                       self._c_p_real_13, self._c_p_real_14, self._c_p_real_15, self._c_p_real_16,
                                       self._c_p_real_17, self._c_p_real_18, self._c_p_real_19, self._c_p_real_20,
                                       self._c_p_real_21]) * 1000

        self._c_p_av_1 = [1.1000, 1.0533, 1.0371, 1.0289, 1.0239, 1.0206, 1.0182, 1.0164, 1.0151, 1.0139]
        self._c_p_av_2 = [1.1095, 1.0592, 1.0418, 1.0330, 1.0277, 1.0241, 1.0215, 1.0196, 1.0181, 1.0169]
        self._c_p_av_3 = [1.1212, 1.0679, 1.0495, 1.0401, 1.0345, 1.0307, 1.0279, 1.0259, 1.0243, 1.0230]
        self._c_p_av_4 = [1.1345, 1.0786, 1.0592, 1.0494, 1.0434, 1.0394, 1.0366, 1.0344, 1.0328, 1.0314]
        self._c_p_av_5 = [1.1489, 1.0905, 1.0703, 1.0600, 1.0538, 1.0497, 1.0467, 1.0445, 1.0427, 1.0413]
        self._c_p_av_6 = [1.1638, 1.1032, 1.0822, 1.0716, 1.0651, 1.0608, 1.0577, 1.0554, 1.0536, 1.0521]
        self._c_p_av_7 = [1.1790, 1.1162, 1.0945, 1.0834, 1.0768, 1.0723, 1.0691, 1.0667, 1.0648, 1.0633]
        self._c_p_av_8 = [1.1941, 1.1292, 1.1068, 1.0954, 1.0885, 1.0839, 1.0805, 1.0781, 1.0761, 1.0746]
        self._c_p_av_9 = [1.2090, 1.1420, 1.1188, 1.1071, 1.1000, 1.0952, 1.0918, 1.0892, 1.0872, 1.0856]
        self._c_p_av_10 = [1.2235, 1.1544, 1.1305, 1.1184, 1.1110, 1.1061, 1.1026, 1.0999, 1.0979, 1.0962]
        self._c_p_av_11 = [1.2375, 1.1663, 1.1417, 1.1292, 1.1216, 1.1165, 1.1129, 1.1102, 1.1080, 1.1063]
        self._c_p_av_12 = [1.2509, 1.1777, 1.1523, 1.1394, 1.1316, 1.1264, 1.1227, 1.1199, 1.1177, 1.1159]
        self._c_p_av_13 = [1.2637, 1.1884, 1.1623, 1.1491, 1.1411, 1.1357, 1.1319, 1.1290, 1.1268, 1.1250]
        self._c_p_av_14 = [1.2758, 1.1986, 1.1718, 1.1582, 1.1500, 1.1445, 1.1406, 1.1376, 1.1353, 1.1335]
        self._c_p_av_15 = [1.2873, 1.2081, 1.1807, 1.1668, 1.1584, 1.1528, 1.1488, 1.1457, 1.1434, 1.1415]
        self._c_p_av_16 = [1.2981, 1.2172, 1.1892, 1.1749, 1.1663, 1.1606, 1.1565, 1.1534, 1.1509, 1.1490]
        self._c_p_av_17 = [1.3082, 1.2257, 1.1971, 1.1826, 1.1738, 1.1679, 1.1637, 1.1605, 1.1581, 1.1561]
        self._c_p_av_18 = [1.3177, 1.2336, 1.2045, 1.1897, 1.1807, 1.1748, 1.1705, 1.1672, 1.1647, 1.1627]
        self._c_p_av_19 = [1.3266, 1.2410, 1.2113, 1.1963, 1.1872, 1.1811, 1.1767, 1.1734, 1.1708, 1.1688]
        self._c_p_av_20 = [1.3349, 1.2477, 1.2175, 1.2022, 1.1929, 1.1867, 1.1823, 1.1789, 1.1763, 1.1742]
        self._c_p_av_21 = [1.3426, 1.2537, 1.2229, 1.2073, 1.1979, 1.1915, 1.1870, 1.1836, 1.1809, 1.1788]
        self._c_p_av_arr = np.array([self._c_p_av_1, self._c_p_av_2, self._c_p_av_3, self._c_p_av_4,
                                     self._c_p_av_5, self._c_p_av_6, self._c_p_av_7, self._c_p_av_8,
                                     self._c_p_av_9, self._c_p_av_10, self._c_p_av_11, self._c_p_av_12,
                                     self._c_p_av_13, self._c_p_av_14, self._c_p_av_15, self._c_p_av_16,
                                     self._c_p_av_17, self._c_p_av_18, self._c_p_av_19, self._c_p_av_20,
                                     self._c_p_av_21]) * 1000
        self._temp_arr = np.array(np.linspace(0, 2000, 21)) + 273
        self._alpha_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self._c_p_real_interp = interp2d(self._alpha_arr, self._temp_arr, self._c_p_real_arr)
        self._c_p_av_interp = interp2d(self._alpha_arr, self._temp_arr, self._c_p_av_arr)

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
        self._c_p = self._c_p_real_func(self._T, alpha=value)
        self._k = self._c_p / (self._c_p - self._R)
        self._c_p_av = self._c_p_av_func(self._T, alpha=value)
        self._k_av = self._c_p_av / (self._c_p_av - self._R)
        self._c_p_av_int = self._c_p_av_int_func(self._T1, self._T2, alpha=value)
        self._k_av_int = self._c_p_av_int / (self._c_p_av_int - self._R)

    def mu(self, T):
        return 17.6e-6 * (T / 273) ** 0.68

    def lam(self, T):
        return 0.0244 * (T / 273) ** 0.82

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
        """Истинная удельная теплоемкость продуктов сгорания природного газа"""
        alpha = kwargs['alpha']
        return self._c_p_real_interp(alpha, T)[0]

    def _c_p_av_func(self, T, **kwargs):
        """Средняя удельная теплоемкость продуктов сгорания природного газа"""
        alpha = kwargs['alpha']
        return self._c_p_av_interp(alpha, T)[0]

    def _c_p_av_int_func(self, T1, T2, **kwargs):
        """Средняя удельная теплоемкость продуктов сгорания природного газа в интервале температур"""
        alpha = kwargs['alpha']
        T0 = 273
        return (self._c_p_av_func(T2, alpha=alpha) * (T2 - T0) -
                self._c_p_av_func(T1, alpha=alpha) * (T1 - T0)) / (T2 - T1)


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    gas = NaturalGasCombustionProducts()
    gas.T1 = 300
    temp = np.linspace(300, 1800, 30)
    gas.alpha = 7.5
    c_p_av = []
    c_p_real = []

    for T in temp:
        gas.T = T
        gas.T2 = T
        c_p_av.append(gas.c_p_av_int)
        c_p_real.append(gas.c_p)

    plt.plot(temp, c_p_real, color='red', label='real')
    plt.plot(temp, c_p_av, color='blue', label='av')
    plt.legend()
    plt.grid()
    plt.show()
