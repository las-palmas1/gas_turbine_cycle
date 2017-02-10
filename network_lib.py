import numpy as np
from abc import ABCMeta, abstractmethod, abstractproperty
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
            if self._alpha != np.inf and self._previous_state._alpha != np.inf:
                self._alpha = self.previous_state.alpha + relax_coef * (self.alpha - self.previous_state.alpha)
            self._g_fuel = self.previous_state.g_fuel + relax_coef * (self.g_fuel - self.previous_state.g_fuel)

    @classmethod
    def _get_residual(cls, old_value, current_value):
        if old_value != np.inf and current_value != np.inf:
            return abs(old_value - current_value) / current_value
        elif old_value == np.inf and current_value == np.inf:
            return 0
        else:
            return 1

    def get_max_residual(self):
        T_res = 1
        p_res = 1
        alpha_res = 1
        if self.previous_state.check() and self.check():
            T_res = abs(self.T_stag - self._previous_state.T_stag) / self.T_stag
            p_res = abs(self.p_stag - self._previous_state.p_stag) / self.p_stag
            alpha_res = self._get_residual(self._previous_state.alpha, self.alpha)
        result = max(T_res, p_res, alpha_res)
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
        return self._T_stag is not None and self._p_stag is not None and self._g is not None and \
               self.alpha is not None


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
        if self._previous_state.check() and self.check() and self._previous_state.L_inlet != 0:
            L_inlet_res = abs(self._previous_state._L_inlet - self._L_inlet) / self._L_inlet
            L_outlet_res = abs(self._previous_state._L_outlet - self._L_outlet) / self._L_outlet
        if self._previous_state.check() and self.check() and self._previous_state.L_inlet == 0 and self.L_inlet == 0:
            L_inlet_res = 0
            L_outlet_res = 0
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
