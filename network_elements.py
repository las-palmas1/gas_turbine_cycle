from gas import *
import gas_dynamics as gd
import numpy as np
import functions as func
from abc import ABCMeta, abstractmethod
import copy
import enum
import typing
import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


class ConnectionType(enum.Enum):
    GasDynamic = 0
    Mechanical = 1


class Connection(metaclass=ABCMeta):
    def __init__(self):
        self._previous_state = None

    @abstractmethod
    def update_previous_state(self):
        pass

    @property
    def previous_state(self):
        return self._previous_state

    @abstractmethod
    def update_current_state(self, relax_coef):
        pass

    @abstractmethod
    def get_max_residual(self):
        pass

    def check(self):
        pass

    @abstractmethod
    def log_state(self):
        pass

    @classmethod
    def _rnd(cls, number, ndigits):
        if number is not None:
            return round(number, ndigits)
        else:
            return None


class GasDynamicConnection(Connection):
    def __init__(self, alpha=np.inf, T_stag=None, p_stag=None, g=1, g_fuel=0):
        Connection.__init__(self)
        self._T_stag = T_stag
        self._p_stag = p_stag
        self._g = g
        self._g_fuel = g_fuel
        self._alpha = alpha
        self._previous_state = copy.deepcopy(self)

    def update_previous_state(self):
        self._previous_state = copy.deepcopy(self)

    def update_current_state(self, relax_coef=1):
        if self.previous_state.check() and self.check():
            self._T_stag = self.previous_state.T_stag + relax_coef * (self.T_stag - self.previous_state.T_stag)
            self._p_stag = self.previous_state.p_stag + relax_coef * (self.p_stag - self.previous_state.p_stag)
            self._g = self.previous_state.g + relax_coef * (self.g - self.previous_state.g)

    def get_max_residual(self):
        T_res = 1
        p_res = 1
        if self.previous_state.check() and self.check():
            T_res = abs(self.T_stag - self._previous_state.T_stag) / self.T_stag
            p_res = abs(self.p_stag - self._previous_state.p_stag) / self.p_stag
        result = max(T_res, p_res)
        return result

    def log_state(self):
        logging.debug('T_stag = %.2f,  p_stag = %s,  g = %.3f,  alpha = %.2f,  g_fuel = %.3f' %
                     (self.T_stag, self._rnd(self.p_stag, 3), self.g, self.alpha, self.g_fuel))

    @property
    def T_stag(self):
        return self._T_stag

    @T_stag.setter
    def T_stag(self, value):
        self._T_stag = value

    @property
    def p_stag(self):
        return self._p_stag

    @p_stag.setter
    def p_stag(self, value):
        self._p_stag = value

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, value):
        self._g = value

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value

    @property
    def g_fuel(self):
        return self._g_fuel

    @g_fuel.setter
    def g_fuel(self, value):
        self._g_fuel = value

    def check(self):
        return self._T_stag is not None and self._p_stag is not None and self._g is not None


class MechanicalConnection(Connection):
    def __init__(self, eta=0.99):
        Connection.__init__(self)
        self._L_inlet = None
        self._L_outlet = None
        self._eta = eta
        self._previous_state = copy.deepcopy(self)

    def update_previous_state(self):
        self._previous_state = copy.deepcopy(self)

    def update_current_state(self, relax_coef=1):
        if self._previous_state.check() and self.check():
            self._L_outlet = self._previous_state._L_outlet + relax_coef * (self._L_outlet -
                                                                            self._previous_state._L_outlet)
            self._L_inlet = self._previous_state._L_inlet + relax_coef * (self._L_inlet -
                                                                          self._previous_state._L_inlet)

    def get_max_residual(self):
        L_inlet_res = 1
        L_outlet_res = 1
        if self._previous_state.check() and self.check():
            L_inlet_res = abs(self._previous_state._L_inlet - self._L_inlet) / self._L_inlet
            L_outlet_res = abs(self._previous_state._L_outlet - self._L_outlet) / self._L_outlet
        return max(L_inlet_res, L_outlet_res)

    def log_state(self):
        logging.debug('L_inlet = %s,  eta = %s' % (self._rnd(self.L_inlet, 3), self._eta))

    def check(self):
        return self.L_inlet is not None and self.L_outlet is not None

    @property
    def L_inlet(self):
        return self._L_inlet

    @L_inlet.setter
    def L_inlet(self, value):
        self._L_inlet = value
        self._L_outlet = value * self._eta

    @property
    def L_outlet(self):
        return self._L_outlet

    @L_outlet.setter
    def L_outlet(self, value):
        self._L_outlet = value
        self._L_inlet = value / self._eta


class Port(metaclass=ABCMeta):
    def __init__(self):
        self._linked_connection = None

    @abstractmethod
    def _linked_connection_get(self):
        pass

    @abstractmethod
    def _linked_connection_set(self, value):
        pass

    linked_connection = abstractproperty(_linked_connection_get, _linked_connection_set)


class GasDynamicPort(Port):
    def __init__(self):
        Port.__init__(self)

    def _linked_connection_get(self) -> GasDynamicConnection:
        return self._linked_connection

    def _linked_connection_set(self, value: GasDynamicConnection):
        self._linked_connection = value

    linked_connection = property(_linked_connection_get, _linked_connection_set)


class MechanicalPort(Port):
    def __init__(self):
        Port.__init__(self)

    def _linked_connection_get(self) -> MechanicalConnection:
        return self._linked_connection

    def _linked_connection_set(self, value: MechanicalConnection):
        self._linked_connection = value

    linked_connection = property(_linked_connection_get, _linked_connection_set)


class Unit(metaclass=ABCMeta):

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def update_connection_current_state(self, relax_coef):
        pass


class Compressor(Unit):
    def __init__(self, pi_c, work_fluid=Air(), eta_stag_p=0.89, precision=0.01):
        self.gd_inlet_port = GasDynamicPort()
        self.gd_outlet_port = GasDynamicPort()
        self.m_inlet_port = MechanicalPort()
        self.eta_stag_p = eta_stag_p
        self.pi_c = pi_c
        self.work_fluid = work_fluid
        self.precision = precision
        self._k = self.work_fluid.k_av_int
        self._k_old = None
        self._eta_stag = None
        self._L = None

    @property
    def k_old(self):
        return self._k_old

    @property
    def k(self):
        return self._k

    @property
    def eta_stag(self):
        return self._eta_stag

    @property
    def L(self):
        return self._L

    def _check(self):
        return self.gd_inlet_port.linked_connection.check() and self.pi_c is not None and self.eta_stag_p is not None

    @property
    def T_stag_in(self):
        return self.gd_inlet_port.linked_connection.T_stag

    @T_stag_in.setter
    def T_stag_in(self, value):
        self.gd_inlet_port.linked_connection.T_stag = value

    @property
    def p_stag_in(self):
        return self.gd_inlet_port.linked_connection.p_stag

    @p_stag_in.setter
    def p_stag_in(self, value):
        self.gd_inlet_port.linked_connection.p_stag = value

    @property
    def g_in(self):
        return self.gd_inlet_port.linked_connection.g

    @g_in.setter
    def g_in(self, value):
        self.gd_inlet_port.linked_connection.g = value

    @property
    def T_stag_out(self):
        return self.gd_outlet_port.linked_connection.T_stag

    @T_stag_out.setter
    def T_stag_out(self, value):
        self.gd_outlet_port.linked_connection.T_stag = value

    @property
    def p_stag_out(self):
        return self.gd_outlet_port.linked_connection.p_stag

    @p_stag_out.setter
    def p_stag_out(self, value):
        self.gd_outlet_port.linked_connection.p_stag = value

    @property
    def g_out(self):
        return self.gd_outlet_port.linked_connection.g

    @g_out.setter
    def g_out(self, value):
        self.gd_outlet_port.linked_connection.g = value

    def update_connection_current_state(self, relax_coef=1):
        if self._check():
            self.gd_outlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_outlet_port connection:')
            self.gd_outlet_port.linked_connection.log_state()
            self.m_inlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of m_inlet_port connection:')
            self.m_inlet_port.linked_connection.log_state()

    def update(self, relax_coef=1):
        if self._check():
            self._k_res = 1
            self.work_fluid.__init__()
            self.work_fluid.T1 = self.T_stag_in
            while self._k_res >= self.precision:
                self._eta_stag = func.eta_comp_stag(self.pi_c, self._k, self.eta_stag_p)
                self.work_fluid.T2 = self.T_stag_in * (1 + (self.pi_c ** ((self._k - 1) / self._k) - 1)) / self._eta_stag
                self.T_stag_out = self.work_fluid.T2
                self._k_old = self._k
                self._k = self.work_fluid.k_av_int
                self._k_res = abs(self._k - self._k_old) / self._k_old
            self._L = self.work_fluid.c_p_av_int * (self.T_stag_out - self.T_stag_in)
            self.p_stag_out = self.p_stag_in * self.pi_c
            self.g_out = 1
            self.m_inlet_port.linked_connection.L_outlet = self._L
            self.gd_outlet_port.linked_connection.alpha = self.gd_inlet_port.linked_connection.alpha
            self.gd_outlet_port.linked_connection.g_fuel = self.gd_inlet_port.linked_connection.g_fuel


class Turbine(Unit):
    def __init__(self, work_fluid=KeroseneCombustionProducts(), eta_stag_p=0.91, precision=0.01):
        self.gd_inlet_port = GasDynamicPort()
        self.gd_outlet_port = GasDynamicPort()
        self.m_comp_outlet_port = MechanicalPort()
        self.m_load_outlet_port = MechanicalPort()
        self.eta_stag_p = eta_stag_p
        self.precision = precision
        self.work_fluid = work_fluid
        self._k = self.work_fluid.k_av_int
        self._k_old = None
        self._k_res = None
        self._pi_t = None
        self._eta_stag = None
        self._L = None
        self._pi_t = None
        self._pi_t_res = 1
        self._pi_t_old = None

    @property
    def k(self):
        return self._k

    @property
    def k_old(self):
        return self._k_old

    @property
    def L(self):
        return self._L

    @property
    def pi_t(self):
        return self._pi_t

    @property
    def eta_stag(self):
        return self._eta_stag

    @property
    def T_stag_in(self):
        return self.gd_inlet_port.linked_connection.T_stag

    @T_stag_in.setter
    def T_stag_in(self, value):
        self.gd_inlet_port.linked_connection.T_stag = value

    @property
    def p_stag_in(self):
        return self.gd_inlet_port.linked_connection.p_stag

    @p_stag_in.setter
    def p_stag_in(self, value):
        self.gd_inlet_port.linked_connection.p_stag = value

    @property
    def g_in(self):
        return self.gd_inlet_port.linked_connection.g

    @g_in.setter
    def g_in(self, value):
        self.gd_inlet_port.linked_connection.g = value

    @property
    def T_stag_out(self):
        return self.gd_outlet_port.linked_connection.T_stag

    @T_stag_out.setter
    def T_stag_out(self, value):
        self.gd_outlet_port.linked_connection.T_stag = value

    @property
    def p_stag_out(self):
        return self.gd_outlet_port.linked_connection.p_stag

    @p_stag_out.setter
    def p_stag_out(self, value):
        self.gd_outlet_port.linked_connection.p_stag = value

    @property
    def g_out(self):
        return self.gd_outlet_port.linked_connection.g

    @g_out.setter
    def g_out(self, value):
        self.gd_outlet_port.linked_connection.g = value

    @property
    def alpha(self):
        return self.gd_inlet_port.linked_connection.alpha

    @alpha.setter
    def alpha(self, value):
        self.gd_inlet_port.linked_connection.alpha = value

    def _check(self):
        return self.gd_inlet_port.linked_connection.check() \
               and self.eta_stag_p is not None \
               and self.alpha is not None \
               and self.alpha != np.inf

    def _check_power_turbine(self):
        return self._check() \
               and self.m_comp_outlet_port.linked_connection.L_inlet is not None \
               and self.gd_outlet_port.linked_connection.p_stag is not None and \
               self.m_load_outlet_port.linked_connection.L_inlet != 0

    def _check_comp_turbine_p_in(self):
        return self._check() \
               and self.m_comp_outlet_port.linked_connection.L_inlet is not None \
               and self.m_load_outlet_port.linked_connection.L_inlet == 0

    def _check_comp_turbine_p_out(self):
        return self.gd_outlet_port.linked_connection.p_stag is not None \
               and self.gd_inlet_port.linked_connection.T_stag is not None \
               and self.gd_inlet_port.linked_connection.g is not None \
               and self.m_comp_outlet_port.linked_connection.L_inlet is not None \
               and self.m_load_outlet_port.linked_connection.L_inlet == 0

    def update_connection_current_state(self, relax_coef=1):
        if self._check_power_turbine():
            self.m_load_outlet_port.linked_connection.update_current_state(relax_coef)
            self.gd_outlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of m_load_port connection:')
            self.m_load_outlet_port.linked_connection.log_state()
            logging.debug('New state of gd_outlet_port connection')
            self.gd_outlet_port.linked_connection.log_state()
        elif self._check_comp_turbine_p_in():
            self.gd_outlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_outlet_port connection')
            self.gd_outlet_port.linked_connection.log_state()
        elif self._check_comp_turbine_p_out():
            self.gd_outlet_port.linked_connection.update_current_state(relax_coef)
            self.gd_inlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_outlet_port connection')
            self.gd_outlet_port.linked_connection.log_state()
            logging.debug('New state of gd_inlet_port connection')
            self.gd_inlet_port.linked_connection.log_state()

    def _compute_compressor_turbine(self):
        self._k_res = 1
        self._pi_t_res = 1
        self.work_fluid.__init__()
        self.work_fluid.alpha = self.alpha
        self.work_fluid.T1 = self.T_stag_in
        self.g_out = self.g_in
        self.gd_outlet_port.linked_connection.g_fuel = self.gd_inlet_port.linked_connection.g_fuel
        self._L = self.m_comp_outlet_port.linked_connection.L_inlet / self.g_in
        while self._k_res >= self.precision:
            self.T_stag_out = self.T_stag_in - self._L / self.work_fluid.c_p_av_int
            self.work_fluid.T2 = self.T_stag_out
            self._k_old = self._k
            self._k = self.work_fluid.k_av_int
            self._k_res = abs(self._k - self._k_old) / self._k_old
        self._pi_t = (1 - self._L / (self.T_stag_in * self.work_fluid.c_p_av_int * self.eta_stag_p)) ** \
                     (self._k / (1 - self._k))
        while self._pi_t_res >= self.precision:
            self._eta_stag = func.eta_turb_stag(self._pi_t, self._k, self.eta_stag_p)
            self._pi_t_old = self._pi_t
            self._pi_t = (1 - self._L / (self.T_stag_in * self.work_fluid.c_p_av_int * self._eta_stag)) ** \
                         (self._k / (1 - self._k))
            self._pi_t_res = abs(self._pi_t - self._pi_t_old) / self._pi_t_old
        self.gd_outlet_port.linked_connection.alpha = self.alpha

    def update(self):
        if self._check_power_turbine():
            self._k_res = 1
            self.work_fluid.__init__()
            self.work_fluid.alpha = self.alpha
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
            self._L = self.work_fluid.c_p_av_int * (self.T_stag_in - self.T_stag_out)
            self.g_out = self.g_in
            self.gd_outlet_port.linked_connection.g_fuel = self.gd_inlet_port.linked_connection.g_fuel
            self.m_load_outlet_port.linked_connection.L_inlet = self._L * self.g_in - \
                                                                self.m_comp_outlet_port.linked_connection.L_inlet
            self.gd_outlet_port.linked_connection.alpha = self.alpha

        elif self._check_comp_turbine_p_in():
            self._compute_compressor_turbine()
            self.p_stag_out = self.p_stag_in / self._pi_t

        elif self._check_comp_turbine_p_out():
            self._compute_compressor_turbine()
            self.p_stag_in = self.p_stag_out * self._pi_t


class CombustionChamber(Unit):
    def __init__(self, Q_n, l0, alpha_out_init=2, precision=0.01, eta_burn=0.98, sigma_comb=0.98, g_outflow=0.01,
                 g_cooling=0.04, g_return=0.02, work_fluid_in=Air(), work_fluid_out=KeroseneCombustionProducts()):
        self.gd_inlet_port = GasDynamicPort()
        self.gd_outlet_port = GasDynamicPort()
        self.work_fluid_in = work_fluid_in
        self.work_fluid_out = work_fluid_out
        self.work_fluid_out_T0 = self.work_fluid_out
        self.alpha_out_init = alpha_out_init
        self.precision = precision
        self.eta_burn = eta_burn
        self.Q_n = Q_n
        self.l0 = l0
        self.sigma_comb = sigma_comb
        self.g_outflow = g_outflow
        self.g_cooling = g_cooling
        self.g_return = g_return
        self._alpha_res = 1
        self._alpha_out_old = None

    @property
    def T_stag_in(self):
        return self.gd_inlet_port.linked_connection.T_stag

    @T_stag_in.setter
    def T_stag_in(self, value):
        self.gd_inlet_port.linked_connection.T_stag = value

    @property
    def p_stag_in(self):
        return self.gd_inlet_port.linked_connection.p_stag

    @p_stag_in.setter
    def p_stag_in(self, value):
        self.gd_inlet_port.linked_connection.p_stag = value

    @property
    def g_in(self):
        return self.gd_inlet_port.linked_connection.g

    @g_in.setter
    def g_in(self, value):
        self.gd_inlet_port.linked_connection.g = value

    @property
    def g_fuel_in(self):
        return self.gd_inlet_port.linked_connection.g_fuel

    @g_fuel_in.setter
    def g_fuel_in(self, value):
        self.gd_inlet_port.linked_connection.g_fuel = value

    @property
    def T_stag_out(self):
        return self.gd_outlet_port.linked_connection.T_stag

    @T_stag_out.setter
    def T_stag_out(self, value):
        self.gd_outlet_port.linked_connection.T_stag = value

    @property
    def p_stag_out(self):
        return self.gd_outlet_port.linked_connection.p_stag

    @p_stag_out.setter
    def p_stag_out(self, value):
        self.gd_outlet_port.linked_connection.p_stag = value

    @property
    def g_out(self):
        return self.gd_outlet_port.linked_connection.g

    @g_out.setter
    def g_out(self, value):
        self.gd_outlet_port.linked_connection.g = value

    @property
    def alpha_out(self):
        return self.gd_outlet_port.linked_connection.alpha

    @alpha_out.setter
    def alpha_out(self, value):
        self.gd_outlet_port.linked_connection.alpha = value

    @property
    def g_fuel_out(self):
        return self.gd_outlet_port.linked_connection.g_fuel

    @g_fuel_out.setter
    def g_fuel_out(self, value):
        self.gd_outlet_port.linked_connection.g_fuel = value

    def _check(self):
        return self.gd_inlet_port.linked_connection.check() and \
               self.alpha_out_init is not None and \
               self.eta_burn is not None and \
               self.Q_n is not None and \
               self.l0 is not None and \
               self.sigma_comb is not None and \
               self.T_stag_out is not None and \
               self.g_cooling is not None and \
               self.g_outflow is not None and \
               self.g_return is not None and \
               self.g_fuel_in is not None

    def update_connection_current_state(self, relax_coef=1):
        if self._check():
            self.gd_outlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_outlet_port connection')
            self.gd_outlet_port.linked_connection.log_state()

    def update(self):
        if self._check():
            self._alpha_res = 1
            self.work_fluid_in.__init__()
            self.work_fluid_out.__init__()
            self.work_fluid_out_T0.__init__()
            self.work_fluid_out.alpha = self.alpha_out_init
            self.work_fluid_out_T0.alpha = self.alpha_out_init
            self.work_fluid_out.T = self.T_stag_out
            self.work_fluid_out_T0.T = 288
            self.work_fluid_in.T = self.T_stag_in
            while self._alpha_res >= self.precision:
                g_fuel_prime = (self.work_fluid_out.c_p_av * self.T_stag_out -
                                self.work_fluid_in.c_p_av * self.T_stag_in) / \
                                   (self.Q_n * self.eta_burn - self.work_fluid_out.c_p_av * self.T_stag_out +
                                    self.work_fluid_out_T0.c_p_av * 288)
                self.g_out = (1 + self.g_fuel_in + g_fuel_prime) * (1 - self.g_cooling - self.g_outflow) + \
                            self.g_return
                self._alpha_out_old = self.work_fluid_out.alpha
                self.alpha_out = 1 / (self.l0 * (self.g_fuel_in + g_fuel_prime))
                self.g_fuel_out = self.g_fuel_in + g_fuel_prime
                self.work_fluid_out.alpha = self.alpha_out
                self.work_fluid_out_T0.alpha = self.alpha_out
                self._alpha_res = abs(self._alpha_out_old - self.alpha_out) / self.alpha_out
            self.p_stag_out = self.p_stag_in * self.sigma_comb


class Inlet(Unit):
    def __init__(self, sigma=0.99, work_fluid=Air()):
        self.sigma = sigma
        self.gd_inlet_port = GasDynamicPort()
        self.gd_outlet_port = GasDynamicPort()
        self.work_fluid = work_fluid

    @property
    def T_stag_in(self):
        return self.gd_inlet_port.linked_connection.T_stag

    @T_stag_in.setter
    def T_stag_in(self, value):
        self.gd_inlet_port.linked_connection.T_stag = value

    @property
    def p_stag_in(self):
        return self.gd_inlet_port.linked_connection.p_stag

    @p_stag_in.setter
    def p_stag_in(self, value):
        self.gd_inlet_port.linked_connection.p_stag = value

    @property
    def g_in(self):
        return self.gd_inlet_port.linked_connection.g

    @g_in.setter
    def g_in(self, value):
        self.gd_inlet_port.linked_connection.g = value

    @property
    def T_stag_out(self):
        return self.gd_outlet_port.linked_connection.T_stag

    @T_stag_out.setter
    def T_stag_out(self, value):
        self.gd_outlet_port.linked_connection.T_stag = value

    @property
    def p_stag_out(self):
        return self.gd_outlet_port.linked_connection.p_stag

    @p_stag_out.setter
    def p_stag_out(self, value):
        self.gd_outlet_port.linked_connection.p_stag = value

    @property
    def g_out(self):
        return self.gd_outlet_port.linked_connection.g

    @g_out.setter
    def g_out(self, value):
        self.gd_outlet_port.linked_connection.g = value

    def _check(self):
        return self.p_stag_in is not None and self.T_stag_in is not None and self.g_in is not None \
               and self.sigma is not None

    def update_connection_current_state(self, relax_coef=1):
        if self._check():
            self.gd_outlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_outlet_port connection')
            self.gd_outlet_port.linked_connection.log_state()

    def update(self):
        if self._check():
            self.p_stag_out = self.p_stag_in * self.sigma
            self.T_stag_out = self.T_stag_in
            self.g_out = self.g_in
            self.gd_outlet_port.linked_connection.alpha = self.gd_inlet_port.linked_connection.alpha
            self.gd_outlet_port.linked_connection.g_fuel = self.gd_inlet_port.linked_connection.g_fuel


class Outlet(Unit):
    def __init__(self, sigma=0.99, work_fluid=KeroseneCombustionProducts()):
        self.gd_inlet_port = GasDynamicPort()
        self.gd_outlet_port = GasDynamicPort()
        self.sigma = sigma
        self.work_fluid = work_fluid

    @property
    def T_stag_in(self):
        return self.gd_inlet_port.linked_connection.T_stag

    @T_stag_in.setter
    def T_stag_in(self, value):
        self.gd_inlet_port.linked_connection.T_stag = value

    @property
    def p_stag_in(self):
        return self.gd_inlet_port.linked_connection.p_stag

    @p_stag_in.setter
    def p_stag_in(self, value):
        self.gd_inlet_port.linked_connection.p_stag = value

    @property
    def g_in(self):
        return self.gd_inlet_port.linked_connection.g

    @g_in.setter
    def g_in(self, value):
        self.gd_inlet_port.linked_connection.g = value

    @property
    def T_stag_out(self):
        return self.gd_outlet_port.linked_connection.T_stag

    @T_stag_out.setter
    def T_stag_out(self, value):
        self.gd_outlet_port.linked_connection.T_stag = value

    @property
    def p_stag_out(self):
        return self.gd_outlet_port.linked_connection.p_stag

    @p_stag_out.setter
    def p_stag_out(self, value):
        self.gd_outlet_port.linked_connection.p_stag = value

    @property
    def g_out(self):
        return self.gd_outlet_port.linked_connection.g

    @g_out.setter
    def g_out(self, value):
        self.gd_outlet_port.linked_connection.g = value

    @property
    def alpha(self):
        return self.gd_inlet_port.linked_connection.alpha

    @alpha.setter
    def alpha(self, value):
        self.gd_inlet_port.linked_connection.alpha = value

    def _check1(self):
        return self.sigma is not None and self.p_stag_out

    def _check2(self):
        return self.T_stag_in is not None

    def update_connection_current_state(self, relax_coef=1):
        if self._check1() and self._check2():
            self.gd_inlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_outlet_port connection')
            self.gd_outlet_port.linked_connection.log_state()
            logging.debug('New state of gd_inlet_port connection')
            self.gd_inlet_port.linked_connection.log_state()

    def update(self):
        if self._check2():
            self.T_stag_out = self.T_stag_in
            self.gd_outlet_port.linked_connection.alpha = self.alpha
            self.g_out = self.g_in
        if self._check1() and self._check2():
            self.T_stag_out = self.T_stag_in
            self.gd_outlet_port.linked_connection.alpha = self.alpha
            self.g_out = self.g_in
            self.p_stag_in = self.p_stag_out / self.sigma
            self.gd_outlet_port.linked_connection.g_fuel = self.gd_inlet_port.linked_connection.g_fuel


class Atmosphere(Unit):
    def __init__(self, p0=1e5, T0=288, lam_in=0.04, work_fluid_in=KeroseneCombustionProducts(), work_fluid_out=Air()):
        self.p0 = p0
        self.T0 = T0
        self.lam_in = lam_in
        self.work_fluid_in = work_fluid_in
        self.work_fluid_out = work_fluid_out
        self.gd_inlet_port = GasDynamicPort()
        self.gd_outlet_port = GasDynamicPort()

    @property
    def T_stag_in(self):
        return self.gd_inlet_port.linked_connection.T_stag

    @T_stag_in.setter
    def T_stag_in(self, value):
        self.gd_inlet_port.linked_connection.T_stag = value

    @property
    def p_stag_in(self):
        return self.gd_inlet_port.linked_connection.p_stag

    @p_stag_in.setter
    def p_stag_in(self, value):
        self.gd_inlet_port.linked_connection.p_stag = value

    @property
    def T_stag_out(self):
        return self.gd_outlet_port.linked_connection.T_stag

    @T_stag_out.setter
    def T_stag_out(self, value):
        self.gd_outlet_port.linked_connection.T_stag = value

    @property
    def p_stag_out(self):
        return self.gd_outlet_port.linked_connection.p_stag

    @p_stag_out.setter
    def p_stag_out(self, value):
        self.gd_outlet_port.linked_connection.p_stag = value

    def _check1(self):
        return self.lam_in is not None and self.p0 is not None and self.T0 is not None

    def _check2(self):
        return self.T_stag_in is not None

    def update_connection_current_state(self, relax_coef=1):
        if self._check1() and self._check2():
            self.gd_inlet_port.linked_connection.update_current_state(relax_coef)
            logging.debug('New state of gd_inlet_port connection')
            self.gd_inlet_port.linked_connection.log_state()

    def update(self):
        if self._check1():
            self.T_stag_out = self.T0
            self.p_stag_out = self.p0
        if self._check1() and self._check2():
            self.T_stag_out = self.T0
            self.p_stag_out = self.p0
            self.work_fluid_in.__init__()
            self.work_fluid_out.__init__()
            self.work_fluid_in.T = self.T_stag_in
            self.p_stag_in = self.p0 / gd.GasDynamicFunctions.pi_lam(self.lam_in, self.work_fluid_in.k)


class Load(Unit):
    def __init__(self, power: float =0):
        self.power = power
        self.m_inlet_port = MechanicalPort()
        self._G_air = None

    @property
    def G_air(self):
        return self._G_air

    @property
    def L(self):
        return self.m_inlet_port.linked_connection.L_outlet

    @L.setter
    def L(self, value):
        self.m_inlet_port.linked_connection.L_outlet = value

    def update_connection_current_state(self, relax_coef=1):
        logging.debug('New state of m_inlet_port connection')
        self.m_inlet_port.linked_connection.log_state()

    def update(self):
        if self.power != 0 and self.L is not None and self.L != 0:
            self._G_air = self.power / self.L
        elif self.power == 0:
            self.L = 0


class NetworkSolver:
    def __init__(self, unit_arr: typing.List[Unit], relax_coef=1, precision=0.01, max_iter_number=50):
        self._connection_arr = []
        self._unit_arr = unit_arr
        self.relax_coef = relax_coef
        self.precision = precision
        self.max_iter_number = max_iter_number
        self._residual_arr = []

    def create_connection(self, outlet_port: Port, inlet_port: Port, connection_type: ConnectionType):
        if connection_type == ConnectionType.GasDynamic:
            connection = GasDynamicConnection()
            outlet_port.linked_connection = connection
            inlet_port.linked_connection = connection
            self._connection_arr.append(connection)
        elif connection_type == ConnectionType.Mechanical:
            connection = MechanicalConnection()
            outlet_port.linked_connection = connection
            inlet_port.linked_connection = connection
            self._connection_arr.append(connection)

    def solve(self):
        for i in range(self.max_iter_number):
            logging.info('Iteration %s\n' % i)
            self._update_previous_connections_state(self._connection_arr)
            self._update_units_state(self._unit_arr, self.relax_coef)
            self._residual_arr.append(self._get_max_residual(self._connection_arr))
            logging.info('MAX RESIDUAL = %.4f\n' % (self._get_max_residual(self._connection_arr)))
            if self._is_converged(self.precision, self._connection_arr):
                return
        raise RuntimeError('Convergence is not obtained')

    @classmethod
    def _update_previous_connections_state(cls, connection_arr: typing.List[Connection]):
        for i in connection_arr:
            i.update_previous_state()

    @classmethod
    def _update_units_state(cls, unit_arr: typing.List[Unit], relax_coef=1):
        for i in unit_arr:
            logging.info(str(i) + ' ' + 'updating')
            i.update()
            i.update_connection_current_state(relax_coef)

    @classmethod
    def _get_max_residual(cls, connection_arr: typing.List[Connection]):
        result = connection_arr[0].get_max_residual()
        for i in connection_arr:
            if i.get_max_residual() > result:
                result = i.get_max_residual()
        return result

    @classmethod
    def _is_converged(cls, precision, connection_arr: typing.List[Connection]):
        def is_valid(connection: Connection):
            max_residual = connection.get_max_residual()
            return max_residual < precision

        for i in connection_arr:
            if not is_valid(i):
                return False
        return True


if __name__ == '__main__':
    # turb = Turbine()
    # g_con1 = GasDynamicConnection()
    # g_con2 = GasDynamicConnection()
    # m_con1 = MechanicalConnection()
    # m_con2 = MechanicalConnection()
    # turb.gd_inlet_port.linked_connection = g_con1
    # turb.gd_outlet_port.linked_connection = g_con2
    # turb.m_comp_outlet_port.linked_connection = m_con1
    # turb.m_load_outlet_port.linked_connection = m_con2
    # turb.p_stag_in = 5e5
    # turb.T_stag_in = 1600
    # turb.g_in = 0.98
    # turb.alpha = 2.5
    # turb.eta_stag_p = 0.91
    # turb.m_comp_outlet_port.linked_connection.L_outlet = 500e3
    # # turb.m_load_outlet.L_outlet = 0
    # turb.p_stag_out = 1.1e5
    # turb.update()
    # print(turb.k)
    # print(turb.eta_stag)
    # print(turb.L)
    # print(turb.pi_t)
    # print(turb.p_stag_in)
    # print(turb.p_stag_out)
    # print(turb.T_stag_out)
    # print(turb.m_load_outlet_port.linked_connection.L_inlet)
    atmosphere = Atmosphere()
    inlet = Inlet()
    comp = Compressor(pi_c=5)
    comb_chamber = CombustionChamber(Q_n=43e6, l0=14.61)
    turbine = Turbine()
    load = Load(power=2.3e6)
    outlet = Outlet()
    unit_arr = [comb_chamber, atmosphere, inlet, comp, turbine, outlet, load]
    solver = NetworkSolver(unit_arr)
    solver.create_connection(atmosphere.gd_outlet_port, inlet.gd_inlet_port, ConnectionType.GasDynamic)
    solver.create_connection(inlet.gd_outlet_port, comp.gd_inlet_port, ConnectionType.GasDynamic)
    solver.create_connection(comp.gd_outlet_port, comb_chamber.gd_inlet_port, ConnectionType.GasDynamic)
    solver.create_connection(comb_chamber.gd_outlet_port, turbine.gd_inlet_port, ConnectionType.GasDynamic)
    solver.create_connection(turbine.m_comp_outlet_port, comp.m_inlet_port, ConnectionType.Mechanical)
    solver.create_connection(turbine.gd_outlet_port, outlet.gd_inlet_port, ConnectionType.GasDynamic)
    solver.create_connection(turbine.m_load_outlet_port, load.m_inlet_port, ConnectionType.Mechanical)
    solver.create_connection(outlet.gd_outlet_port, atmosphere.gd_inlet_port, ConnectionType.GasDynamic)
    comb_chamber.T_stag_out = 1600
    turbine.p_stag_out = 170e3
    solver.solve()











