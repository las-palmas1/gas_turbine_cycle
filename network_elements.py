from gas import *
import numpy as np
import functions as func
from abc import ABCMeta, abstractmethod
import copy


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


class GasDynamicConnection(Connection):
    def __init__(self, T_stag=None, p_stag=None, g=None):
        Connection.__init__(self)
        self._T_stag = T_stag
        self._p_stag = p_stag
        self._g = g
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
    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def _update_connections_previous_state(self):
        pass

    @abstractmethod
    def _update_connections_current_state(self):
        pass


class Compressor(Unit):
    def __init__(self, gd_inlet_port: GasDynamicPort = GasDynamicPort(),
                 gd_outlet_port: GasDynamicPort = GasDynamicPort(),
                 m_inlet_port: MechanicalPort = MechanicalPort()):
        self.gd_inlet_port = gd_inlet_port
        self.gd_outlet_port = gd_outlet_port
        self.m_inlet_port = m_inlet_port
        self.eta_stag_p = None
        self.pi_c = None
        self.work_fluid = Air()
        self._k = self.work_fluid.k_av_int
        self._k_old = None
        self._dk_rel = 1
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

    def _update_connections_previous_state(self):
        self.gd_outlet_port.linked_connection.update_previous_state()
        self.gd_outlet_port.linked_connection.update_previous_state()
        self.m_inlet_port.linked_connection.update_previous_state()

    def _update_connections_current_state(self, relax_coef=1):
        self.gd_inlet_port.linked_connection.update_current_state(relax_coef=relax_coef)
        self.gd_outlet_port.linked_connection.update_current_state(relax_coef=relax_coef)
        self.m_inlet_port.linked_connection.update_current_state(relax_coef=relax_coef)

    def update(self, relax_coef=1):
        if self._check():
            self._update_connections_previous_state()
            self.work_fluid.__init__()
            self.work_fluid.T1 = self.T_stag_in
            while self._dk_rel >= 0.01:
                self._eta_stag = func.eta_comp_stag(self.pi_c, self._k, self.eta_stag_p)
                self.work_fluid.T2 = self.T_stag_in * (1 + (self.pi_c ** ((self._k - 1) / self._k))) / self._eta_stag
                self.T_stag_out = self.work_fluid.T2
                self._k_old = self._k
                self._k = self.work_fluid.k_av_int
                self._dk_rel = abs(self._k - self._k_old) / self._k_old
            self._L = self.work_fluid.c_p_av_int * (self.T_stag_out - self.T_stag_in)
            self.p_stag_out = self.p_stag_in * self.pi_c
            self.g_out = 1
            self.m_inlet_port.L_outlet = self._L
            self._update_connections_current_state(relax_coef=relax_coef)


class Turbine(Unit):
    def __init__(self, gd_inlet_port: GasDynamicPort = GasDynamicPort(),
                 gd_outlet_port: GasDynamicPort = GasDynamicPort(),
                 m_comp_outlet_port: MechanicalPort = MechanicalPort(),
                 m_load_outlet_port: MechanicalPort = MechanicalPort()):
        self.gd_inlet_port = gd_inlet_port
        self.gd_outlet_port = gd_outlet_port
        self.m_comp_outlet_port = m_comp_outlet_port
        self.m_load_outlet_port = m_load_outlet_port
        self.eta_stag_p = None
        self.alpha = None
        self.work_fluid = KeroseneCombustionProducts()
        self._k = self.work_fluid.k_av_int
        self._k_old = None
        self._dk_rel = 1
        self._pi_t = None
        self._eta_stag = None
        self._L = None
        self._pi_t = None
        self._dpi_t_rel = 1
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

    def _check(self):
        return self.gd_inlet_port.linked_connection.check() \
               and self.eta_stag_p is not None \
               and self.alpha is not None

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

    def _compute_compressor_turbine(self):
        self.work_fluid.__init__()
        self.work_fluid.alpha = self.alpha
        self.work_fluid.T1 = self.T_stag_in
        self.g_out = self.g_in
        self._L = self.m_comp_outlet_port.linked_connection.L_inlet / self.g_in
        while self._dk_rel >= 0.01:
            self.T_stag_out = self.T_stag_in - self._L / self.work_fluid.c_p_av_int
            self.work_fluid.T2 = self.T_stag_out
            self._k_old = self._k
            self._k = self.work_fluid.k_av_int
            self._dk_rel = abs(self._k - self._k_old) / self._k_old
        self._pi_t = (1 - self._L / (self.T_stag_in * self.work_fluid.c_p_av_int * self.eta_stag_p)) ** \
                     (self._k / (1 - self._k))
        while self._dpi_t_rel >= 0.01:
            self._eta_stag = func.eta_turb_stag(self._pi_t, self._k, self.eta_stag_p)
            self._pi_t_old = self._pi_t
            self._pi_t = (1 - self._L / (self.T_stag_in * self.work_fluid.c_p_av_int * self._eta_stag)) ** \
                         (self._k / (1 - self._k))
            self._dpi_t_rel = abs(self._pi_t - self._pi_t_old) / self._pi_t_old

    def _update_connections_previous_state(self):
        self.gd_inlet_port.linked_connection.update_previous_state()
        self.gd_outlet_port.linked_connection.update_previous_state()
        self.m_load_outlet_port.linked_connection.update_previous_state()
        self.m_comp_outlet_port.linked_connection.update_previous_state()

    def _update_connections_current_state(self, relax_coef=1):
        self.gd_inlet_port.linked_connection.update_current_state(relax_coef=relax_coef)
        self.gd_outlet_port.linked_connection.update_current_state(relax_coef=relax_coef)
        self.m_load_outlet_port.linked_connection.update_current_state(relax_coef=relax_coef)
        self.m_comp_outlet_port.linked_connection.update_current_state(relax_coef=relax_coef)

    def update(self, relax_coef=1):
        if self._check_power_turbine():
            self._update_connections_previous_state()
            self.work_fluid.__init__()
            self.work_fluid.alpha = self.alpha
            self.work_fluid.T1 = self.T_stag_in
            self._pi_t = self.p_stag_in / self.p_stag_out
            while self._dk_rel >= 0.01:
                self._eta_stag = func.eta_turb_stag(self._pi_t, self._k, self.eta_stag_p)
                self.work_fluid.T2 = self.T_stag_in * (1 - (1 - self._pi_t **
                                                            ((1 - self._k) / self._k)) * self._eta_stag)
                self.T_stag_out = self.work_fluid.T2
                self._k_old = self._k
                self._k = self.work_fluid.k_av_int
                self._dk_rel = abs(self._k - self._k_old) / self._k_old
            self._L = self.work_fluid.c_p_av_int * (self.T_stag_in - self.T_stag_out)
            self.g_out = self.g_in
            self.m_load_outlet_port.linked_connection.L_inlet = self._L * self.g_in - \
                                                                self.m_comp_outlet_port.linked_connection.L_inlet
            self._update_connections_current_state(relax_coef=relax_coef)

        elif self._check_comp_turbine_p_in():
            self._update_connections_previous_state()
            self._compute_compressor_turbine()
            self.p_stag_out = self.p_stag_in / self._pi_t
            self._update_connections_current_state(relax_coef=relax_coef)

        elif self._check_comp_turbine_p_out():
            self._update_connections_previous_state()
            self._compute_compressor_turbine()
            self.p_stag_in = self.p_stag_out * self._pi_t
            self._update_connections_current_state(relax_coef=relax_coef)


if __name__ == '__main__':
    turb = Turbine()
    g_con1 = GasDynamicConnection()
    g_con2 = GasDynamicConnection()
    m_con1 = MechanicalConnection()
    m_con2 = MechanicalConnection()
    turb.gd_inlet_port.linked_connection = g_con1
    turb.gd_outlet_port.linked_connection = g_con2
    turb.m_comp_outlet_port.linked_connection = m_con1
    turb.m_load_outlet_port.linked_connection = m_con2
    turb.p_stag_in = 5e5
    turb.T_stag_in = 1600
    turb.g_in = 0.98
    turb.alpha = 2.5
    turb.eta_stag_p = 0.91
    turb.m_comp_outlet_port.linked_connection.L_outlet = 500e3
    # turb.m_load_outlet.L_outlet = 0
    turb.p_stag_out = 1.1e5
    turb.update()
    print(turb.k)
    print(turb.eta_stag)
    print(turb.L)
    print(turb.pi_t)
    print(turb.p_stag_in)
    print(turb.p_stag_out)
    print(turb.T_stag_out)
    print(turb.m_load_outlet_port.linked_connection.L_inlet)











