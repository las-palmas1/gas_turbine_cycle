from .gases import NaturalGasCombustionProducts, KeroseneCombustionProducts, Air, IdealGas
import unittest
import numpy as np


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

