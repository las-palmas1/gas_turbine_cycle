import logging
import numpy as np

from ..tools.gas_dynamics import GasDynamicFunctions as gd
from .network_lib import *
from ..gases import *
from ..tools import functions as func

logging.basicConfig(format='%(levelname)s: %(message)s', filemode='w', filename='cycle.log', level=logging.INFO)


class Compressor(GasDynamicUnit, MechEnergyConsumingUnit):
    def __init__(self, pi_c, work_fluid: IdealGas=Air(), eta_stag_p=0.89, precision=0.01):
        GasDynamicUnit.__init__(self)
        MechEnergyConsumingUnit.__init__(self)
        self.eta_stag_p = eta_stag_p
        self.pi_c = pi_c
        self.work_fluid = work_fluid
        self.precision = precision
        self._k = self.work_fluid.k_av_int
        self._k_res = 1
        self._k_old = None
        self._eta_stag = None

    @property
    def k_old(self):
        return self._k_old

    @property
    def k(self):
        return self._k

    @property
    def k_res(self):
        return self._k_res

    @property
    def eta_stag(self):
        return self._eta_stag

    def check_input(self) -> bool:
        res = (self.T_stag_in is not None) and \
              (self.p_stag_in is not None) and \
              (self.alpha_in is not None) and \
              (self.g_in is not None) and \
              (self.g_fuel_in is not None)
        return res

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.pres_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)

        self.make_port_output(self.labour_consume_port)
        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.pres_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)

    def update(self, relax_coef=1):
        if self.check_input():
            self.work_fluid.__init__()
            self.work_fluid.T1 = self.T_stag_in
            while self._k_res >= self.precision:
                self._eta_stag = func.eta_comp_stag(self.pi_c, self._k, self.eta_stag_p)
                self.work_fluid.T2 = self.T_stag_in * (1 + (self.pi_c ** ((self._k - 1) / self._k) - 1) /
                                                       self._eta_stag)
                self.T_stag_out = self.work_fluid.T2
                self._k_old = self._k
                self._k = self.work_fluid.k_av_int
                self._k_res = abs(self._k - self._k_old) / self._k_old
            self.consumable_labour = self.work_fluid.c_p_av_int * (self.T_stag_out - self.T_stag_in)
            self.p_stag_out = self.p_stag_in * self.pi_c
            self.g_out = self.g_in
            self.alpha_out = self.alpha_in
            self.g_fuel_out = self.g_fuel_in
        else:
            logging.info('Some of input parameters are not specified.')


class Turbine(GasDynamicUnit, MechEnergyGeneratingUnit):
    def __init__(self, work_fluid: IdealGas=KeroseneCombustionProducts(), eta_stag_p=0.91, eta_m=0.99, precision=0.01,
                 eta_r=0.99, **kwargs):
        """
        :param work_fluid: рабочее тело турбины
        :param eta_stag_p: политропическй КПД
        :param eta_m: механический КПД
        :param eta_r: КПД редуктора
        :param precision: точность расчета турбины
        :param kwargs: p_stag_out_init - необходимо задать для силовой турбины и компрессорной \n
                турбины, находящейся по потоку ниже силовой турбины
        """
        GasDynamicUnit.__init__(self)
        MechEnergyGeneratingUnit.__init__(self)
        self.eta_stag_p = eta_stag_p
        self.precision = precision
        self.work_fluid = work_fluid
        self.eta_m = eta_m
        self.eta_r = eta_r
        self._k = self.work_fluid.k_av_int
        self._k_old = None
        self._k_res = None
        self._pi_t = None
        self._eta_stag = None
        self._pi_t = None
        self._pi_t_res = 1
        self._pi_t_old = None
        self._comp_labour = None
        if 'p_stag_out_init' in kwargs:
            self._p_stag_out_init = kwargs['p_stag_out_init']
            self.pres_outlet_port.value = self._p_stag_out_init
        else:
            self._p_stag_out_init = None

    @property
    def k(self):
        return self._k

    @property
    def k_old(self):
        return self._k_old

    @property
    def k_res(self):
        return self._k_res

    @property
    def pi_t(self):
        return self._pi_t

    @property
    def eta_stag(self):
        return self._eta_stag

    def check_upstream_compressor_turbine_behaviour(self) -> bool:
        """Возвращает True, если турбина должна вести себя как турбина компрессора, находящаяся по газовому
        тракту до силовой турбины"""
        cond1 = self.labour_generating_port1.port_type == PortType.Input
        cond2 = self.labour_generating_port2.port_type == PortType.Input
        cond3 = self.pres_inlet_port.port_type == PortType.Input or self.pres_outlet_port.port_type == PortType.Output
        return cond1 and cond2 and cond3

    def check_downstream_compressor_turbine_behaviour(self) -> bool:
        """Возвращает True, если турбина должна вести себя как турбина компрессора, находящаяся по газовому
        тракту после силовой турбины"""
        cond1 = self.labour_generating_port1.port_type == PortType.Input
        cond2 = self.labour_generating_port2.port_type == PortType.Input
        cond3 = self.pres_outlet_port.port_type == PortType.Input or self.pres_inlet_port.port_type == PortType.Output
        return cond1 and cond2 and cond3

    def check_power_turbine_behaviour(self):
        """Возвоащает True, если турбина ведет себя как силовая"""
        cond1 = self.labour_generating_port1.port_type == PortType.Input
        cond2 = self.labour_generating_port2.port_type == PortType.Output
        cond3 = self.labour_generating_port1.port_type == PortType.Output
        cond4 = self.labour_generating_port2.port_type == PortType.Input
        return (cond1 and cond2) or (cond3 and cond4)

    def check_input(self):
        cond1 = self.T_stag_in is not None
        cond2 = self.g_in is not None
        cond3 = self.g_fuel_in is not None
        cond4 = self.alpha_in is not None
        cond5 = False
        cond6 = False
        cond7 = False
        if self.check_downstream_compressor_turbine_behaviour():
            cond5 = self.p_stag_out is not None
            cond6 = self.gen_labour1 is not None
            cond7 = self.gen_labour2 is not None
        if self.check_upstream_compressor_turbine_behaviour():
            cond5 = self.p_stag_in is not None
            cond6 = self.gen_labour1 is not None
            cond7 = self.gen_labour2 is not None
        if self.check_power_turbine_behaviour():
            cond5 = self.p_stag_in is not None
            cond6 = self.p_stag_out is not None
            cond7 = self.gen_labour1 is not None or self.gen_labour2 is not None
        return cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)
        self.make_port_input(self.alpha_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.alpha_outlet_port)

        if self.check_downstream_compressor_turbine_behaviour():
            self.make_port_input(self.pres_outlet_port)
            self.make_port_input(self.labour_generating_port1)
            self.make_port_input(self.labour_generating_port2)
            self.make_port_output(self.pres_inlet_port)
        if self.check_upstream_compressor_turbine_behaviour():
            self.make_port_input(self.pres_inlet_port)
            self.make_port_input(self.labour_generating_port1)
            self.make_port_input(self.labour_generating_port2)
            self.make_port_output(self.pres_outlet_port)
        if self.check_power_turbine_behaviour():
            self.make_port_input(self.pres_inlet_port)
            self.make_port_input(self.pres_outlet_port)

    def _compute_compressor_turbine(self):
        self._k_res = 1
        self._pi_t_res = 1
        self.work_fluid.__init__()
        self.work_fluid.alpha = self.alpha_in
        self.work_fluid.T1 = self.T_stag_in
        self.total_labour = (self.gen_labour1 + self.gen_labour2) / (self.g_in * self.eta_m)
        while self._k_res >= self.precision:
            self.T_stag_out = self.T_stag_in - self.total_labour / self.work_fluid.c_p_av_int
            self.work_fluid.T2 = self.T_stag_out
            self._k_old = self._k
            self._k = self.work_fluid.k_av_int
            self._k_res = abs(self._k - self._k_old) / self._k_old
        self._pi_t = (1 - self.total_labour / (self.T_stag_in * self.work_fluid.c_p_av_int * self.eta_stag_p)) ** \
                     (self._k / (1 - self._k))
        while self._pi_t_res >= self.precision:
            self._eta_stag = func.eta_turb_stag(self._pi_t, self._k, self.eta_stag_p)
            self._pi_t_old = self._pi_t
            self._pi_t = (1 - self.total_labour / (self.T_stag_in * self.work_fluid.c_p_av_int * self._eta_stag)) ** \
                         (self._k / (1 - self._k))
            self._pi_t_res = abs(self._pi_t - self._pi_t_old) / self._pi_t_old

    def update(self):
        if self.check_power_turbine_behaviour():
            assert self._p_stag_out_init is not None, 'For power turbine computing the initial approximation of ' \
                                                      'outlet stagnation pressure must must be set'
        if self.check_downstream_compressor_turbine_behaviour():
            assert self._p_stag_out_init is not None, 'For downstream compressor turbine computing the initial ' \
                                                      'approximation of outlet stagnation pressure must must be set'
        if self.check_input():
            self.alpha_out = self.alpha_in
            self.g_out = self.g_in
            self.g_fuel_out = self.g_fuel_in
            if self.check_power_turbine_behaviour():
                self._k_res = 1
                self.work_fluid.__init__()
                self.work_fluid.alpha = self.alpha_in
                self.work_fluid.T1 = self.T_stag_in
                self._pi_t = self.p_stag_in / self.p_stag_out
                while self._k_res >= self.precision:
                    self._eta_stag = func.eta_turb_stag(self._pi_t, self._k, self.eta_stag_p)
                    self.work_fluid.T2 = self.T_stag_in * (1 - (1 - self._pi_t **
                                                                ((1 - self._k) / self._k)) * self._eta_stag)
                    self.T_stag_out = self.work_fluid.T2
                    self._k_old = self._k
                    self._k = self.work_fluid.k_av_int
                    self._k_res = abs(self._k - self._k_old) / self._k_old
                self.total_labour = self.work_fluid.c_p_av_int * (self.T_stag_in - self.T_stag_out)
                if self.labour_generating_port2.port_type == PortType.Output:
                    self.gen_labour2 = self.eta_r * (self.total_labour * self.eta_m * self.g_in - self.gen_labour1)
                elif self.labour_generating_port1.port_type == PortType.Output:
                    self.gen_labour1 = self.eta_r * (self.total_labour * self.eta_m * self.g_in - self.gen_labour2)

            elif self.check_upstream_compressor_turbine_behaviour():
                self._compute_compressor_turbine()
                self.p_stag_out = self.p_stag_in / self._pi_t

            elif self.check_downstream_compressor_turbine_behaviour():
                self._compute_compressor_turbine()
                self.p_stag_in = self.p_stag_out * self._pi_t
        else:
            logging.info('Some of input parameters are not specified.')


class Source(GasDynamicUnit):
    """Моделирует возврат в проточную часть части воздуха, отобранного для охлаждения."""
    def __init__(self, work_fluid: IdealGas=KeroseneCombustionProducts(), g_return=0.01, return_fluid: IdealGas=Air(),
                 return_fluid_temp=700):
        """
        :param g_return: относительный расход возвращаемого воздуха (по отношению к расходу на входе в компрессор)
        """
        GasDynamicUnit.__init__(self)
        self.work_fluid = work_fluid
        self.g_return = g_return
        self.return_fluid = return_fluid
        self.return_fluid_temp = return_fluid_temp

    def check_upstream_behaviour(self) -> bool:
        """Возвращает True, если источник должен передавать давление по потоку, т.е. если он находится по
        газовому тракту до силовой турбины"""
        cond1 = self.pres_inlet_port.port_type == PortType.Input
        cond2 = self.pres_outlet_port.port_type == PortType.Output
        return cond1 or cond2

    def check_downstream_behaviour(self) -> bool:
        """Возвращает True, если источник должен передавать давление против потока, т.е. если он находится по
        газовому тракту после силовой турбины"""
        cond1 = self.pres_inlet_port.port_type == PortType.Output
        cond2 = self.pres_outlet_port.port_type == PortType.Input
        return cond1 or cond2

    def check_input(self):
        cond1 = self.T_stag_in is not None
        cond2 = self.alpha_in is not None
        cond3 = self.g_in is not None
        cond4 = self.g_fuel_in is not None
        cond5 = False
        if self.check_upstream_behaviour():
            cond5 = self.p_stag_in is not None
        elif self.check_downstream_behaviour():
            cond5 = self.p_stag_out is not None
        return cond1 and cond2 and cond3 and cond4 and cond5

    def check_input_partially(self):
        """Проверка наличия входных данных для осуществления части расчета юнита"""
        cond1 = self.T_stag_in is not None
        cond2 = self.alpha_in is not None
        cond3 = self.g_in is not None
        cond4 = self.g_fuel_in is not None
        return cond1 and cond2 and cond3 and cond4

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)

        if self.check_upstream_behaviour():
            self.make_port_input(self.pres_inlet_port)
            self.make_port_output(self.pres_outlet_port)
        elif self.check_downstream_behaviour():
            self.make_port_output(self.pres_inlet_port)
            self.make_port_input(self.pres_outlet_port)

    def _compute(self):
        self.work_fluid.__init__()
        self.work_fluid.alpha = self.alpha_in
        self.alpha_out = 1 / (self.work_fluid.l0 * (self.g_fuel_in / (self.g_in + self.g_return - self.g_fuel_in)))
        self.g_out = self.g_in + self.g_return

        (self.mix_temp_new, self.mixture, self.c_p_comb_products_true,
         self.c_p_air_true, self._mix_temp, self.temp_mix_res) = func.get_mixture_temp(
            comb_products=self.work_fluid,
            air=self.return_fluid,
            temp_comb_products=self.T_stag_in,
            temp_air=self.return_fluid_temp,
            g_comb_products=self.g_in,
            g_air=self.g_return,
            alpha_mixture=self.alpha_out
        )

        self.g_fuel_out = self.g_fuel_in
        self.T_stag_out = self._mix_temp

    def update(self):
        if self.check_input():
            self._compute()
            if self.check_upstream_behaviour():
                self.p_stag_out = self.p_stag_in
            elif self.check_downstream_behaviour():
                self.p_stag_in = self.p_stag_out
        elif self.check_input_partially():
            self._compute()
        else:
            logging.info('Some of input parameters are not specified.')


class Sink(GasDynamicUnit):
    """Моделирует отбор воздуха на охлаждение и утечки"""
    def __init__(self, g_cooling=0.04, g_outflow=0.01):
        """
        :param g_cooling: относительный расход воздуха на охлаждение
        :param g_outflow: относительный расход воздуха на утечки (все по отношению к расходу на входе в компрессор)
        """
        GasDynamicUnit.__init__(self)
        self.g_cooling = g_cooling
        self.g_outflow = g_outflow

    def check_input(self):
        cond1 = self.T_stag_in is not None
        cond2 = self.p_stag_in is not None
        cond3 = self.alpha_in is not None
        cond4 = self.g_in is not None
        cond5 = self.g_fuel_in is not None
        return cond1 and cond2 and cond3 and cond4 and cond5

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.pres_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.pres_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.alpha_outlet_port)

    def update(self):
        if self.check_input():
            self.alpha_out = self.alpha_in
            self.g_fuel_out = self.g_fuel_in
            self.T_stag_out = self.T_stag_in
            self.p_stag_out = self.p_stag_in
            self.g_out = self.g_in - self.g_cooling - self.g_outflow
        else:
            logging.info('Some of input parameters are not specified.')


class CombustionChamber(GasDynamicUnit):
    def __init__(self, T_gas, precision=0.01, eta_burn=0.99, sigma_comb=0.98,
                 work_fluid_in=Air(), work_fluid_out=KeroseneCombustionProducts(), T_fuel=288, **kwargs):
        """
        :param T_gas: температура газа после камеры сгорания
        :param precision:  точноссть расчета камеры
        :param eta_burn: коэффициент полноты горения
        :param sigma_comb: коэффициент сохранения полного давления
        :param work_fluid_in: рабочее тело на входе
        :param work_fluid_out: рабочее тело на выходе
        :param T_fuel: температура топлива.
        :param kwargs: alpha_out_init - начальное приближение для коэффициента избытка воздуха \n
                    p_stag_out_init - начальное приближение для давления на выходе, необходимо задать,
                    если камера сгорания находится после силовой турбины
        """
        GasDynamicUnit.__init__(self)
        self._T_gas = T_gas
        self.work_fluid_in = work_fluid_in
        self.work_fluid_out = work_fluid_out
        self.work_fluid_out_T0 = type(self.work_fluid_out)()
        self.precision = precision
        self.eta_burn = eta_burn
        self.sigma_comb = sigma_comb
        self.T_fuel = T_fuel
        self._alpha_res = 1
        self._alpha_out_old = None
        self._g_fuel_prime = 0
        if 'alpha_out_init' in kwargs:
            self._alpha_out_init = kwargs['alpha_out_init']
            self.alpha_outlet_port.value = self._alpha_out_init
        else:
            self._alpha_out_init = 2.5
            self.alpha_outlet_port.value = self._alpha_out_init
        if 'p_stag_out_init' in kwargs:
            self._p_stag_out_init = kwargs['p_stag_out_init']
            self.pres_outlet_port.value = self._p_stag_out_init
        else:
            self._p_stag_out_init = None

    @property
    def Q_n(self):
        return self.work_fluid_out.Q_n

    @property
    def l0(self):
        return self.work_fluid_out.l0

    def check_upstream_behaviour(self) -> bool:
        """Возвращает True, если камера должна передавать давление по потоку, т.е. если она находится по
        газовому тракту до силовой турбины"""
        cond1 = self.pres_inlet_port.port_type == PortType.Input
        cond2 = self.pres_outlet_port.port_type == PortType.Output
        return cond1 or cond2

    def check_downstream_behaviour(self) -> bool:
        """Возвращает True, если камера должна передавать давление против потока, т.е. если она находится по
        газовому тракту после силовой турбины"""
        cond1 = self.pres_inlet_port.port_type == PortType.Output
        cond2 = self.pres_outlet_port.port_type == PortType.Input
        return cond1 or cond2

    def check_input(self):
        cond1 = self.T_stag_in is not None
        cond2 = self.alpha_in is not None
        cond3 = self.g_in is not None
        cond4 = self.g_fuel_in is not None
        cond5 = False
        if self.check_upstream_behaviour():
            cond5 = self.p_stag_in is not None
        elif self.check_downstream_behaviour():
            cond5 = self.p_stag_out is not None
        return cond1 and cond2 and cond3 and cond4 and cond5

    def check_input_partially(self):
        cond1 = False
        if self.check_upstream_behaviour():
            cond1 = self.p_stag_in is not None
        elif self.check_downstream_behaviour():
            cond1 = self.p_stag_out is not None
        return cond1

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)

        if self.check_upstream_behaviour():
            self.make_port_input(self.pres_inlet_port)
            self.make_port_output(self.pres_outlet_port)
        elif self.check_downstream_behaviour():
            self.make_port_output(self.pres_inlet_port)
            self.make_port_input(self.pres_outlet_port)

    @property
    def g_fuel_prime(self):
        """Значение относительного расхода в данной камере сгорания"""
        return self._g_fuel_prime

    @property
    def alpha_res(self):
        """Невязка по коэффициенту избытка воздуха"""
        return self._alpha_res

    @property
    def alpha_out_old(self):
        return self._alpha_out_old

    def update(self):
        if self.check_downstream_behaviour():
            assert self._p_stag_out_init is not None, 'For downstream combustion chamber computing the initial ' \
                                                      'approximation of outlet stagnation pressure must be set'
        if self.check_input():
            self._alpha_res = 1
            self.T_stag_out = self._T_gas
            self.work_fluid_in.__init__()
            self.work_fluid_out.__init__()
            self.work_fluid_out_T0.__init__()

            self.work_fluid_in.alpha = self.alpha_in
            self.work_fluid_out.alpha = self.alpha_out
            self.work_fluid_out_T0.alpha = self.alpha_out

            self.work_fluid_in.T = self.T_stag_in
            self.work_fluid_out.T = self.T_stag_out
            self.work_fluid_out_T0.T = 288

            while self._alpha_res >= self.precision:
                self._g_fuel_prime = (self.work_fluid_out.c_p_av * self.T_stag_out -
                                      self.work_fluid_in.c_p_av * self.T_stag_in) / \
                                     (self.Q_n * self.eta_burn - self.work_fluid_out.c_p_av * self.T_stag_out +
                                      self.work_fluid_out_T0.c_p * 288)
                self.g_out = self.g_in * (1 + self._g_fuel_prime)
                self._alpha_out_old = self.work_fluid_out.alpha
                self.alpha_out = 1 / (self.l0 * (self.g_fuel_prime * self.g_in) / (self.g_in - self.g_fuel_in))
                self.g_fuel_out = self.g_fuel_in + self._g_fuel_prime * self.g_in
                self.work_fluid_out.alpha = self.alpha_out
                self.work_fluid_out_T0.alpha = self.alpha_out
                self._alpha_res = abs(self._alpha_out_old - self.alpha_out) / self.alpha_out

            if self.check_upstream_behaviour():
                self.p_stag_out = self.p_stag_in * self.sigma_comb
            else:
                self.p_stag_in = self.p_stag_out / self.sigma_comb
        elif self.check_input_partially():
            if self.check_upstream_behaviour():
                self.p_stag_out = self.p_stag_in * self.sigma_comb
            else:
                self.p_stag_in = self.p_stag_out / self.sigma_comb
        else:
            logging.info('Some of input parameters are not specified.')


class Inlet(GasDynamicUnit):
    def __init__(self, sigma=0.99, work_fluid=Air()):
        GasDynamicUnit.__init__(self)
        self.sigma = sigma
        self.work_fluid = work_fluid

    def check_input(self) -> bool:
        cond1 = self.T_stag_in is not None
        cond2 = self.p_stag_in is not None
        cond3 = self.alpha_in is not None
        cond4 = self.g_in is not None
        cond5 = self.g_fuel_in is not None
        return cond1 and cond2 and cond3 and cond4 and cond5

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.pres_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.pres_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)

    def update(self):
        if self.check_input():
            self.p_stag_out = self.p_stag_in * self.sigma
            self.T_stag_out = self.T_stag_in
            self.alpha_out = self.alpha_in
            self.g_fuel_out = self.g_fuel_in
            self.g_out = self.g_in
            self.g_out = self.g_in
        else:
            logging.info('Some of input parameters are not specified.')


class Outlet(GasDynamicUnitStaticOutlet):
    def __init__(self, sigma=0.99, c_out=100, work_fluid=KeroseneCombustionProducts()):
        """
        :param sigma: Коэффициент сохранения полного давления.
        :param c_out: Скорость на выходе из выходного устройства.
        :param work_fluid:
        """
        GasDynamicUnitStaticOutlet.__init__(self)
        self.sigma = sigma
        self.c_out = c_out
        self.a_cr_out = None
        self.lam_out = None
        self.work_fluid = work_fluid

    def check_input(self) -> bool:
        cond1 = self.T_stag_in is not None
        cond2 = self.p_out is not None
        cond3 = self.alpha_in is not None
        cond4 = self.g_in is not None
        cond5 = self.g_fuel_in is not None
        return cond1 and cond2 and cond3 and cond4 and cond5 and cond2

    def check_input_partially(self) -> bool:
        """Проверка наличия входных данных для осуществления части расчета юнита"""
        cond1 = self.p_stag_out is not None
        return cond1

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)
        self.make_port_input(self.stat_pres_outlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)
        self.make_port_output(self.stat_temp_outlet_port)

        self.make_port_output(self.pres_inlet_port)
        self.make_port_output(self.pres_outlet_port)

    def update(self):
        if self.check_input():
            self.work_fluid.T = self.T_stag_in
            self.T_stag_out = self.T_stag_in
            self.g_out = self.g_in
            self.alpha_out = self.alpha_in
            self.g_fuel_out = self.g_fuel_in
            self.a_cr_out = gd.a_cr(self.T_stag_out, self.work_fluid.k, self.work_fluid.R)
            self.lam_out = self.c_out / self.a_cr_out
            self.p_stag_out = self.p_out / gd.pi_lam(self.lam_out, self.work_fluid.k)
            self.T_out = self.T_stag_out * gd.tau_lam(self.lam_out, self.work_fluid.k)
            self.p_stag_in = self.p_stag_out / self.sigma
        elif self.check_input_partially():
            self.p_stag_out = self.p_out / gd.pi_lam(self.lam_out, self.work_fluid.k)
            self.p_stag_in = self.p_stag_out / self.sigma
        else:
            logging.info('Some of input parameters are not specified.')


class Atmosphere(GasDynamicUnitStaticInlet):
    def __init__(self, p0=1e5, T0=288, work_fluid_in: IdealGas=KeroseneCombustionProducts(),
                 work_fluid_out: IdealGas=Air(), **kwargs):
        """
        :param p0: атмосферное давление
        :param T0: темперактура атмосферы
        :param work_fluid_in: рабочее тело на входе в атмосферу
        :param work_fluid_out: рабочее тело на выходе из атмосферы (на входе во входной устройство)
        :param kwargs: T_stag_in_init - начальное прибилижение для температуры выходных газов
        """
        GasDynamicUnitStaticInlet.__init__(self)
        self.p0 = p0
        self.T0 = T0
        self.work_fluid_in = work_fluid_in
        self.work_fluid_out = work_fluid_out
        if 'T_stag_in_init' in kwargs:
            self._T_stag_in_init = kwargs['T_stag_in_init']
            self.temp_inlet_port.value = self._T_stag_in_init
        else:
            self._T_stag_in_init = 600
            self.temp_inlet_port.value = self._T_stag_in_init

    def check_input(self) -> bool:
        return True

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)

        self.make_port_output(self.pres_outlet_port)
        self.make_port_input(self.pres_inlet_port)

        self.make_port_input(self.stat_temp_inlet_port)
        self.make_port_output(self.stat_pres_inlet_port)

    def update(self):
        if self.check_input():
            self.T_stag_out = self.T0
            self.p_stag_out = self.p0
            self.alpha_out = np.inf
            self.g_fuel_out = 0
            self.g_out = 1
            self.work_fluid_in.__init__()
            self.work_fluid_out.__init__()
            self.work_fluid_in.T = self.T_stag_in
            self.p_in = self.p0
        else:
            logging.info('Some of input parameters are not specified.')


class FullExtensionNozzle(GasDynamicUnitStaticOutlet):
    def __init__(self, phi=0.99, work_fluid: IdealGas=KeroseneCombustionProducts(), precision=0.01):
        GasDynamicUnitStaticOutlet.__init__(self)
        self.phi = phi
        self.work_fluid = work_fluid
        self.precision = precision
        self._k = self.work_fluid.k_av_int
        self._c_p = self.work_fluid.c_p_av_int
        self._k_res = 1.
        self._k_old = None
        self.pi_n = None
        self.c_out = None
        self.H_n = None

    def check_input(self):
        cond1 = self.p_stag_in is not None
        cond2 = self.T_stag_in is not None
        cond3 = self.p_out is not None
        cond4 = self.alpha_in is not None
        cond5 = self.g_in is not None
        cond6 = self.g_fuel_in is not None
        return cond1 and cond2 and cond3 and cond4 and cond5 and cond6

    def set_behaviour(self):
        self.make_port_input(self.temp_inlet_port)
        self.make_port_input(self.alpha_inlet_port)
        self.make_port_input(self.g_fuel_inlet_port)
        self.make_port_input(self.g_work_fluid_inlet_port)
        self.make_port_input(self.pres_inlet_port)

        self.make_port_output(self.temp_outlet_port)
        self.make_port_output(self.alpha_outlet_port)
        self.make_port_output(self.g_fuel_outlet_port)
        self.make_port_output(self.g_work_fluid_outlet_port)
        self.make_port_output(self.pres_outlet_port)

        self.make_port_input(self.stat_pres_outlet_port)
        self.make_port_output(self.stat_temp_outlet_port)

    def update(self):
        if self.check_input():
            self.pi_n = self.p_stag_in / self.p_out
            self.work_fluid.alpha = self.alpha_in
            self.work_fluid.T1 = self.T_stag_in
            self.T_stag_out = self.T_stag_in
            self.alpha_out = self.alpha_in
            self.g_out = self.g_in
            self.g_fuel_out = self.g_fuel_in

            while self._k_res >= self.precision:
                self._k_old = self._k
                self.H_n = self._c_p * self.T_stag_in * (1 - self.pi_n ** ((1 - self._k) / self._k))
                self.T_out = self.T_stag_in - self.phi * self.H_n / self._c_p
                self.c_out = self.phi * (self.H_n * 2) ** 0.5
                self.work_fluid.T2 = self.T_out
                self._k = self.work_fluid.k_av_int
                self._c_p = self.work_fluid.c_p_av_int
                self._k_res = abs(self._k_res - self._k_old) / self._k_res

            self.p_stag_out = self.p_out / gd.pi_lam(
                self.c_out / gd.a_cr(self.T_stag_out, self._k, self.work_fluid.R), self._k
            )


class Load(MechEnergyConsumingUnit):
    def __init__(self, power: float =0):
        MechEnergyConsumingUnit.__init__(self)
        self.power = power

    def check_input(self):
        return True

    def set_behaviour(self):
        if self.power == 0:
            self.make_port_output(self.labour_consume_port)
        else:
            self.make_port_input(self.labour_consume_port)

    def update(self):
        if self.power == 0:
            self.consumable_labour = 0
        else:
            pass


# class Regenerator(Unit):
#     def __init__(self, regeneration_rate, sigma_hot=0.99, sigma_cold=0.99, work_fluid_cold=Air(),
#                  work_fluid_hot=KeroseneCombustionProducts()):
#         self.regeneration_rate = regeneration_rate
#         self.sigma_hot = sigma_hot
#         self.sigma_cold = sigma_cold
#         self.hot_gd_inlet_port = GasDynamicPort()
#         self.hot_gd_outlet_port = GasDynamicPort()
#         self.cold_gd_inlet_port = GasDynamicPort()
#         self.cold_gd_outlet_port = GasDynamicPort()
#         self.work_fluid_hot = work_fluid_hot
#         self.work_fluid_cold = work_fluid_cold
#
#     @property
#     def T_stag_hot_in(self):
#         return self.hot_gd_inlet_port.linked_connection.T_stag
#
#     @T_stag_hot_in.setter
#     def T_stag_hot_in(self, value):
#         self.hot_gd_inlet_port.linked_connection.T_stag = value
#
#     @property
#     def p_stag_hot_in(self):
#         return self.hot_gd_inlet_port.linked_connection.p_stag
#
#     @p_stag_hot_in.setter
#     def p_stag_hot_in(self, value):
#         self.hot_gd_inlet_port.linked_connection.p_stag = value
#
#     @property
#     def T_stag_hot_out(self):
#         return self.hot_gd_outlet_port.linked_connection.T_stag
#
#     @T_stag_hot_out.setter
#     def T_stag_hot_out(self, value):
#         self.hot_gd_outlet_port.linked_connection.T_stag = value
#
#     @property
#     def p_stag_hot_out(self):
#         return self.hot_gd_outlet_port.linked_connection.p_stag
#
#     @p_stag_hot_out.setter
#     def p_stag_hot_out(self, value):
#         self.hot_gd_outlet_port.linked_connection.p_stag = value
#
#     @property
#     def T_stag_cold_in(self):
#         return self.cold_gd_inlet_port.linked_connection.T_stag
#
#     @T_stag_cold_in.setter
#     def T_stag_cold_in(self, value):
#         self.cold_gd_inlet_port.linked_connection.T_stag = value
#
#     @property
#     def p_stag_cold_in(self):
#         return self.cold_gd_inlet_port.linked_connection.p_stag
#
#     @p_stag_cold_in.setter
#     def p_stag_cold_in(self, value):
#         self.cold_gd_inlet_port.linked_connection.p_stag = value
#
#     @property
#     def T_stag_cold_out(self):
#         return self.cold_gd_outlet_port.linked_connection.T_stag
#
#     @T_stag_cold_out.setter
#     def T_stag_cold_out(self, value):
#         self.cold_gd_outlet_port.linked_connection.T_stag = value
#
#     @property
#     def p_stag_cold_out(self):
#         return self.cold_gd_outlet_port.linked_connection.p_stag
#
#     @p_stag_cold_out.setter
#     def p_stag_cold_out(self, value):
#         self.cold_gd_outlet_port.linked_connection.p_stag = value
#
#     @property
#     def g_hot(self):
#         return self.hot_gd_inlet_port.linked_connection.g
#
#     @g_hot.setter
#     def g_hot(self, value):
#         self.hot_gd_inlet_port.linked_connection.g = value
#
#     @property
#     def g_cold(self):
#         return self.cold_gd_inlet_port.linked_connection.g
#
#     @g_cold.setter
#     def g_cold(self, value):
#         self.cold_gd_inlet_port.linked_connection.g = value
#
#     @property
#     def alpha_hot(self):
#         return self.hot_gd_inlet_port.linked_connection.alpha
#
#     @alpha_hot.setter
#     def alpha_hot(self, value):
#         self.hot_gd_inlet_port.linked_connection.alpha = value
#
#     @property
#     def alpha_cold(self):
#         return self.cold_gd_inlet_port.linked_connection.alpha
#
#     @alpha_cold.setter
#     def alpha_cold(self, value):
#         self.cold_gd_inlet_port.linked_connection.alpha = value
#
#     def _check1(self):
#         return self.p_stag_cold_in is not None and self.g_hot is not None and self.g_cold is not None\
#                and self.T_stag_cold_in is not None and self.T_stag_hot_in is not None\
#                and self.T_stag_hot_out is not None
#
#     def _check2(self):
#         return self.p_stag_hot_out is not None
#
#     def _compute_output(self):
#         self.T_stag_cold_out = self.regeneration_rate * (self.T_stag_hot_in - self.T_stag_cold_in) + \
#                                self.T_stag_cold_in
#         self.p_stag_cold_out = self.p_stag_cold_in * self.sigma_cold
#         self.hot_gd_outlet_port.linked_connection.alpha = self.alpha_hot
#         self.cold_gd_outlet_port.linked_connection.alpha = self.alpha_cold
#         self.hot_gd_outlet_port.linked_connection.g_fuel = self.hot_gd_inlet_port.linked_connection.g_fuel
#         self.cold_gd_outlet_port.linked_connection.g_fuel = self.cold_gd_inlet_port.linked_connection.g_fuel
#         self.hot_gd_outlet_port.linked_connection.g = self.g_hot
#         self.cold_gd_outlet_port.linked_connection.g = self.g_cold
#         self.T_stag_hot_out = self._get_T_stag_hot_out(self.T_stag_cold_in, self.T_stag_cold_out,
#                                                        self.T_stag_hot_in, self.T_stag_hot_out)
#
#     def update(self):
#         if self._check1():
#             self._compute_output()
#         if self._check1() and self._check2():
#             self._compute_output()
#             self.p_stag_hot_in = self.p_stag_hot_out / self.sigma_hot
#
#     def update_connection_current_state(self, relax_coef=1):
#         if self._check1() and self._check2():
#             self.cold_gd_outlet_port.linked_connection.update_current_state(relax_coef)
#             logging.debug('New state of cold_gd_outlet_port connection')
#             self.cold_gd_outlet_port.linked_connection.log_state()
#             self.hot_gd_outlet_port.linked_connection.update_current_state(relax_coef)
#             logging.info('New state of hot_gd_outlet_port connection')
#             self.hot_gd_outlet_port.linked_connection.log_state()
#             self.hot_gd_inlet_port.linked_connection.update_current_state(relax_coef)
#             logging.info('New state of hot_gd_inlet_port connection')
#             self.hot_gd_inlet_port.linked_connection.log_state()
#
#     def _get_T_stag_hot_out(self, T_stag_cold_in, T_stag_cold_out, T_stag_hot_in, T_stag_hot_out):
#         self.work_fluid_cold.__init__()
#         self.work_fluid_hot.__init__()
#         self.work_fluid_hot.alpha = self.alpha_hot
#         self.work_fluid_cold.T1 = T_stag_cold_in
#         self.work_fluid_cold.T2 = T_stag_cold_out
#         self.work_fluid_hot.T1 = T_stag_hot_in
#         self.work_fluid_hot.T2 = T_stag_hot_out
#         c_p_av_ratio = self.work_fluid_cold.c_p_av_int / self.work_fluid_hot.c_p_av_int
#         g_rel_ratio = self.g_cold / self.g_hot
#         return self.T_stag_hot_in - g_rel_ratio * c_p_av_ratio * (T_stag_cold_out - T_stag_cold_in)
#

if __name__ == '__main__':
    pass















