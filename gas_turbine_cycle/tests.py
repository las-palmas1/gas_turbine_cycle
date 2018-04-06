from .gases import NaturalGasCombustionProducts, KeroseneCombustionProducts, Air, IdealGas
import unittest
import numpy as np
from .tools.functions import get_mixture_temp


def get_partition(fluid: IdealGas, T1=300, T2=1000, num_pnt=10, alpha=2.):
    T_arr = np.linspace(T1, T2, num_pnt)
    dT_arr = T_arr[1:num_pnt] - T_arr[0:num_pnt - 1]
    c_p_av_arr = np.zeros(dT_arr.shape[0])
    for i in range(len(dT_arr)):
        fluid.T1 = T_arr[i]
        fluid.T2 = T_arr[i + 1]
        fluid.alpha = alpha
        c_p_av_arr[i] = fluid.c_p_av_int
    return c_p_av_arr, dT_arr


def get_enthalpy_arr_c_p_av(fluid: IdealGas, T1_arr, dT=200, alpha=2.):
    fluid1 = type(fluid)()
    fluid2 = type(fluid)()
    res = []
    for T1 in T1_arr:
        fluid1.T = T1
        fluid1.alpha = alpha
        fluid2.T = T1 + dT
        fluid2.alpha = alpha
        enthalpy = fluid2.c_p_av * (T1 + dT - fluid2.T0) - fluid1.c_p_av * (T1 - fluid1.T0)
        res.append(enthalpy)
    return res


def get_enthalpy_arr_c_p_av_int(fluid: IdealGas, T1_arr, dT=200, alpha=2.):
    res = []
    for T1 in T1_arr:
        fluid.T1 = T1
        fluid.T2 = T1 + dT
        fluid.alpha = alpha
        enthalpy = fluid.c_p_av_int * dT
        res.append(enthalpy)
    return res


class TestEnthalpyCalculating(unittest.TestCase):
    def setUp(self):
        self.air = Air()
        self.ker = KeroseneCombustionProducts()
        self.ngas = NaturalGasCombustionProducts()
        self.alpha_arr = np.linspace(1.5, 10, 25)
        self.T1_arr = np.linspace(330, 1250, 25)
        self.dT_arr = np.linspace(30, 350, 10)

    def test_air(self):
        for dT in self.dT_arr:
            for alpha in self.alpha_arr:
                enthalpy_c_p_av_arr = get_enthalpy_arr_c_p_av(self.air, self.T1_arr, dT, alpha)
                enthalpy_c_p_av_int_arr = get_enthalpy_arr_c_p_av_int(self.air, self.T1_arr, dT, alpha)
                for enthalpy_c_p_av, enthalpy_c_p_av_int in zip(enthalpy_c_p_av_arr, enthalpy_c_p_av_int_arr):
                    enthalpy_res = abs(enthalpy_c_p_av - enthalpy_c_p_av_int) / enthalpy_c_p_av_int
                    self.assertAlmostEqual(enthalpy_res, 0, places=3)

    def test_kerosene(self):
        for dT in self.dT_arr:
            for alpha in self.alpha_arr:
                enthalpy_c_p_av_arr = get_enthalpy_arr_c_p_av(self.ker, self.T1_arr, dT, alpha)
                enthalpy_c_p_av_int_arr = get_enthalpy_arr_c_p_av_int(self.ker, self.T1_arr, dT, alpha)
                for enthalpy_c_p_av, enthalpy_c_p_av_int in zip(enthalpy_c_p_av_arr, enthalpy_c_p_av_int_arr):
                    enthalpy_res = abs(enthalpy_c_p_av - enthalpy_c_p_av_int) / enthalpy_c_p_av_int
                    self.assertAlmostEqual(enthalpy_res, 0, places=3)

    def test_natural_gas(self):
        for dT in self.dT_arr:
            for alpha in self.alpha_arr:
                enthalpy_c_p_av_arr = get_enthalpy_arr_c_p_av(self.ngas, self.T1_arr, dT, alpha)
                enthalpy_c_p_av_int_arr = get_enthalpy_arr_c_p_av_int(self.ngas, self.T1_arr, dT, alpha)
                for enthalpy_c_p_av, enthalpy_c_p_av_int in zip(enthalpy_c_p_av_arr, enthalpy_c_p_av_int_arr):
                    enthalpy_res = abs(enthalpy_c_p_av - enthalpy_c_p_av_int) / enthalpy_c_p_av_int
                    self.assertAlmostEqual(enthalpy_res, 0, places=3)


class TestAveragingSpecoficHeat(unittest.TestCase):
    def setUp(self):
        self.air = Air()
        self.ngas = NaturalGasCombustionProducts()
        self.ker = KeroseneCombustionProducts()
        self.T1 = 350
        self.T2 = 1600
        self.num_pnt = 5
        self.alpha_arr = np.linspace(1.5, 10, 25)

    def test_kerosene(self):
        for alpha in self.alpha_arr:
            c_p_av_arr, dT_arr = get_partition(self.ker, self.T1, self.T2, self.num_pnt, alpha)
            heat = self.ker.c_p_av_int_func(self.T1, self.T2, alpha=alpha) * (self.T2 - self.T1)
            heat_from_part = (c_p_av_arr * dT_arr).sum()
            heat_res = abs(heat - heat_from_part) / heat_from_part
            self.assertAlmostEqual(heat_res, 0, places=4)

    def test_air(self):
        c_p_av_arr, dT_arr = get_partition(self.ker, self.T1, self.T2, self.num_pnt, self.alpha_arr[0])
        heat = self.ker.c_p_av_int_func(self.T1, self.T2, alpha=self.alpha_arr[0]) * (self.T2 - self.T1)
        heat_from_part = (c_p_av_arr * dT_arr).sum()
        heat_res = abs(heat - heat_from_part) / heat_from_part
        self.assertAlmostEqual(heat_res, 0, places=4)

    def test_natural_gas(self):
        for alpha in self.alpha_arr:
            c_p_av_arr, dT_arr = get_partition(self.ngas, self.T1, self.T2, self.num_pnt, alpha)
            heat = self.ngas.c_p_av_int_func(self.T1, self.T2, alpha=alpha) * (self.T2 - self.T1)
            heat_from_part = (c_p_av_arr * dT_arr).sum()
            heat_res = abs(heat - heat_from_part) / heat_from_part
            self.assertAlmostEqual(heat_res, 0, places=4)


class TestMixture(unittest.TestCase):
    def setUp(self):
        self.precision = 0.0001
        self.air = Air()
        self.ker = KeroseneCombustionProducts()
        self.ngas = NaturalGasCombustionProducts()
        self.T_comb_products = 1400
        self.T_air = 700
        self.g_comb_products_arr = np.linspace(0.5, 1.5, 10)
        self.g_air_arr = np.linspace(0.01, 0.40, 10)
        self.g_fuel_arr = np.linspace(0.01, 0.08, 5)

    def test_kerosene_air_mixture(self):
        for g_comb_products in self.g_comb_products_arr:
            for g_air in self.g_air_arr:
                for g_fuel in self.g_fuel_arr:
                    fuel_content_comp_prod = g_fuel / (g_comb_products - g_fuel)
                    fuel_content_mixture = g_fuel / (g_comb_products + g_air - g_fuel)
                    self.ker.alpha = 1 / (self.ker.l0 * fuel_content_comp_prod)
                    alpha_mixture = 1 / (self.ker.l0 * fuel_content_mixture)
                    (
                        mix_temp_new, mixture, c_p_comb_products_av, c_p_air_av, mix_temp, temp_mix_res
                    ) = get_mixture_temp(
                        self.ker, self.air, self.T_comb_products, self.T_air, g_comb_products, g_air,
                        alpha_mixture, self.precision
                    )
                    mixture.T = mix_temp
                    mixture.alpha = alpha_mixture
                    self.air.T = self.T_air
                    self.ker.T = self.T_comb_products

                    enthalpy_mixtute = mixture.c_p_av * (mix_temp - mixture.T0) * (g_air + g_comb_products)
                    enthalpy_air = self.air.c_p_av * (self.T_air - self.air.T0) * g_air
                    enthalpy_comb_prod = self.ker.c_p_av * (self.T_comb_products - self.ker.T0) * g_comb_products
                    enthalpy_res = abs(enthalpy_comb_prod + enthalpy_air - enthalpy_mixtute) / enthalpy_mixtute
                    self.assertAlmostEqual(enthalpy_res, 0, places=3)