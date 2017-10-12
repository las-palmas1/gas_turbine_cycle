import numpy as np
from abc import ABCMeta, abstractmethod, abstractproperty
import copy
import enum
import typing
import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


class Unit(metaclass=ABCMeta):

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def update_connection_current_state(self, relax_coef):
        pass


class UnitNew:
    def __init__(self):
        self.input_ports: typing.List[PortNew] = []
        "Список входных портов"
        self.output_ports: typing.List[PortNew] = []
        "Список выходных портов"

    def __str__(self):
        return self.__class__.__name__

    def update(self):
        """Пересчитывает значения в связях, подключенных к выходным портам"""
        pass

    def make_port_input(self, port):
        """Меняет тип порта на Input и добавляет в список входных портов"""
        port.make_input()
        self.input_ports.append(port)

    def make_port_output(self, port):
        """Меняет тип порта на Output и добавляет в список входных портов"""
        port.make_output()
        self.output_ports.append(port)

    def update_output_connection_current_state(self, relax_coef):
        """Обновляет текущие значения в связях, подключенных к выходным портам, с учетом релаксации"""
        for port in self.output_ports:
            port.update_connection_current_state(relax_coef)

    def set_behaviour(self) -> bool:
        """
        :return: True, если все порты были настроены; False в противном случае
        Настойка типов всех портов.
        """
        pass


class ConnectionType(enum.Enum):
    GasDynamic = 0
    Mechanical = 1


class PortType(enum.Enum):
    """Тип порта"""
    Input = 0
    "Порт осуществляет доступ к входным для расчета юнита данным. Порт не может принимать значение"
    Output = 1
    "Порт осуществляет доступ к выходным данным. Порт может принимать значение"
    Undefined = 2


class ConnectionNew:
    """Класс соединяющий порты"""
    def __init__(self):
        self.value = None
        "Значение передаваемого параметра"
        self.upstream_port: OutletPort = None
        "Порт следующего по течению или направлению передачи работы юнита"
        self.downstream_port: InletPort = None
        "Порт предыдущего по течению или направлению передачи работы юнита"
        self.upstream_unit: UnitNew = None
        "Следующий по течению или направлению передачи работы юнит"
        self.downstream_unit: UnitNew = None
        "Предыдущий по течению или направлению передачи работы юнит"
        self.previous_value = None
        "Значение передаваемого параметра в предыдущем состоянии"

    def update_previous_state(self):
        self.previous_value = self.value

    def get_residual(self):
        """Возврат значения невязки"""
        return abs(self.value - self.previous_value) / self.value

    def update_current_state(self, relax_coef=1):
        """Пересчитывает текущее значение с учетом релаксации"""
        self.value = self.previous_value + relax_coef * (self.value - self.previous_value)


class PortNew(metaclass=ABCMeta):
    """Класс, через который из юнитов можно осуществлять доступ к связям (Connection)"""
    def __init__(self, unit: UnitNew):
        self._unit = unit
        self._linked_connection: ConnectionNew = None
        self._port_type: PortType = PortType.Undefined

    def get(self):
        """Возвращает хранимое в соединении значении"""
        return self._linked_connection.value

    def set(self, value):
        """Задает хранимое в соединении значении"""
        assert self._port_type == PortType.Output, "You can't set value of parameter in Connection " \
                                                   "object via this port in this unit because it's not output port"
        self._linked_connection.value = value

    def set_connection(self, connection: ConnectionNew):
        """Задание соединение, к которому через порт можно осуществить доступ"""
        pass

    def update_connection_current_state(self, relax_coef=1):
        """Обновляет текущее состояние соединения с учетом коэффициента релаксации"""
        self._linked_connection.update_current_state(relax_coef=relax_coef)

    @abstractmethod
    def make_input(self):
        """Меняет тип порта на Input"""
        pass

    @abstractmethod
    def make_output(self):
        """Меняет тип порта на Output"""
        pass

    @property
    def port_type(self) -> PortType:
        return self._port_type

    @abstractmethod
    def get_connected_port(self):
        """Возвращает порт, с которым данный порт соединен"""
        pass

    @abstractmethod
    def get_connected_port_type(self) -> PortType:
        """Возвращает тип порта, с которым текущий порт соединен"""
        pass


class OutletPort(PortNew):
    """Порт, соответствующий газодинамическому или энергетическому выходу юнита"""
    def __init__(self, unit: UnitNew):
        PortNew.__init__(self, unit)

    def make_input(self):
        self._port_type = PortType.Input
        assert self.get_connected_port_type() != PortType.Input, 'Connected must not have the same type: %s' % \
                                                                 PortType.Input
        if self.get_connected_port_type() == PortType.Undefined:
            self.get_connected_port().make_output()

    def make_output(self):
        self._port_type = PortType.Output
        assert self.get_connected_port_type() != PortType.Output, 'Connected must not have the same type: %s' % \
                                                                  PortType.Output
        if self.get_connected_port_type() == PortType.Undefined:
            self.get_connected_port().make_input()

    def get_connected_port(self) -> PortNew:
        return self._linked_connection.downstream_port

    def get_connected_port_type(self) -> PortType:
        return self._linked_connection.downstream_port.port_type

    def set_connection(self, connection: ConnectionNew):
        self._linked_connection = connection
        self._linked_connection.upstream_port = self
        self._linked_connection.upstream_unit = self._unit


class InletPort(PortNew):
    """Порт, соответствующий газодинамическому или энергетическому входу юнита"""
    def __init__(self, unit: UnitNew):
        PortNew.__init__(self, unit)

    def make_input(self):
        self._port_type = PortType.Input
        assert self.get_connected_port_type() != PortType.Input, 'Connected must not have the same type: %s' % \
                                                                 PortType.Input
        if self.get_connected_port_type() == PortType.Undefined:
            self.get_connected_port().make_output()

    def make_output(self):
        self._port_type = PortType.Output
        assert self.get_connected_port_type() != PortType.Output, 'Connected must not have the same type: %s' % \
                                                                  PortType.Output
        if self.get_connected_port_type() == PortType.Undefined:
            self.get_connected_port().make_input()

    def get_connected_port(self) -> PortNew:
        return self._linked_connection.upstream_port

    def get_connected_port_type(self) -> PortType:
        return self._linked_connection.upstream_port.port_type

    def set_connection(self, connection: ConnectionNew):
        self._linked_connection = connection
        self._linked_connection.downstream_port = self
        self._linked_connection.downstream_unit = self._unit


class GasDynamicUnit(UnitNew):
    """Инициализирует и осуществляет доступ к газодинамическим портам"""
    def __init__(self):
        UnitNew.__init__(self)
        self._temp_inlet_port = InletPort(self)
        self._temp_outlet_port = OutletPort(self)
        self._pres_inlet_port = InletPort(self)
        self._pres_outlet_port = OutletPort(self)
        self._alpha_inlet_port = InletPort(self)
        self._alpha_outlet_port = OutletPort(self)
        self._g_work_fluid_inlet_port = InletPort(self)
        self._g_work_fluid_outlet_port = OutletPort(self)
        self._g_fuel_inlet_port = InletPort(self)
        self._g_fuel_outlet_port = OutletPort(self)

    @property
    def temp_inlet_port(self) -> InletPort:
        """Возвращает порт приема температуры"""
        return self._temp_inlet_port

    @property
    def pres_inlet_port(self) -> InletPort:
        """Возвращает порт приема давления"""
        return self._pres_inlet_port

    @property
    def alpha_inlet_port(self) -> InletPort:
        """Возвращает порт приема коэффициента избытка воздуха"""
        return self._alpha_inlet_port

    @property
    def g_work_fluid_inlet_port(self) -> InletPort:
        """Возвращает порт приема относительного расхода рабочего тела"""
        return self._g_work_fluid_inlet_port

    @property
    def g_fuel_inlet_port(self) -> InletPort:
        """Возвращает порт приема относительного расхода топлива"""
        return self._g_fuel_inlet_port

    @property
    def temp_outlet_port(self) -> OutletPort:
        """Возвращает выходной порт температуры"""
        return self._temp_outlet_port

    @property
    def pres_outlet_port(self) -> OutletPort:
        """Возращает выходной порт давления"""
        return self._pres_outlet_port

    @property
    def alpha_outlet_port(self) -> OutletPort:
        """Возращает выходной порт коэффициента избытка воздуха"""
        return self._alpha_outlet_port

    @property
    def g_work_fluid_outlet_port(self) -> OutletPort:
        """Возвращает выходной порт относительного расхода рабочего тела"""
        return self._g_work_fluid_outlet_port

    @property
    def g_fuel_outlet_port(self) -> OutletPort:
        """Возвращает выходной порт относительного расхода топлива"""
        return self._g_fuel_outlet_port

    @property
    def T_stag_in(self):
        """Температура на входе"""
        return self._temp_inlet_port.get()

    @T_stag_in.setter
    def T_stag_in(self, value):
        self._temp_inlet_port.set(value)

    @property
    def p_stag_in(self):
        """Давление на входе"""
        return self._pres_inlet_port.get()

    @p_stag_in.setter
    def p_stag_in(self, value):
        self._pres_inlet_port.set(value)

    @property
    def alpha_in(self):
        """Коэффициент избытка воздуха на входе"""
        return self._alpha_inlet_port.get()

    @alpha_in.setter
    def alpha_in(self, value):
        self._alpha_inlet_port.set(value)

    @property
    def g_fuel_in(self):
        """Относительный расход топлива на входе"""
        return self._g_fuel_inlet_port.get()

    @g_fuel_in.setter
    def g_fuel_in(self, value):
        self._g_fuel_inlet_port.set(value)

    @property
    def g_in(self):
        """Относительный расход рабочего тела на входе"""
        return self._g_work_fluid_inlet_port.get()

    @g_in.setter
    def g_in(self, value):
        self._g_work_fluid_inlet_port.set(value)

    @property
    def T_stag_out(self):
        """Температура на выходе"""
        return self._temp_outlet_port.get()

    @T_stag_out.setter
    def T_stag_out(self, value):
        self._temp_outlet_port.set(value)

    @property
    def p_stag_out(self):
        """Давление на выходе"""
        return self._pres_outlet_port.get()

    @p_stag_out.setter
    def p_stag_out(self, value):
        self._pres_outlet_port.set(value)

    @property
    def alpha_out(self):
        """Коэффициент избытка воздуха на выходе"""
        return self._alpha_outlet_port.get()

    @alpha_out.setter
    def alpha_out(self, value):
        self._alpha_outlet_port.set(value)

    @property
    def g_fuel_out(self):
        """Относительный расход топлива на выходе"""
        return self._g_fuel_outlet_port.get()

    @g_fuel_out.setter
    def g_fuel_out(self, value):
        self._g_fuel_outlet_port.set(value)

    @property
    def g_out(self):
        """Относительный расход рабочего тела на выходе"""
        return self._g_work_fluid_outlet_port.get()

    @g_out.setter
    def g_out(self, value):
        self._g_work_fluid_outlet_port.set(value)


class MechEnergyConsumingUnit(UnitNew):
    """Осуществляет доступ к портам приема работы юнита, потребляющего механическую энергию"""
    def __init__(self):
        UnitNew.__init__(self)
        self._labour_consume_port = InletPort(self)

    @property
    def labour_consume_port(self) -> InletPort:
        """Возвращает порт приема работы"""
        return self._labour_consume_port

    @property
    def consumable_labour(self):
        """Потребляемая работа"""
        return self._labour_consume_port.get()

    @consumable_labour.setter
    def consumable_labour(self, value):
        self._labour_consume_port.set(value)


class MechEnergyGeneratingUnit(UnitNew):
    """Осуществляет доступ к портам отдачи работы юнита, генерирующего механическую энергию"""
    def __init__(self):
        UnitNew.__init__(self)
        self._labour_generating_port1 = OutletPort(self)
        self._labour_generating_port2 = OutletPort(self)
        self._total_labour = None

    @property
    def total_labour(self):
        """Возвращает суммарную работу, генерируемую юнитом"""
        return self._total_labour

    @total_labour.setter
    def total_labour(self, value):
        self._total_labour = value

    @property
    def labour_generating_port1(self) -> OutletPort:
        """Возвращает первый порт генерации работы"""
        return self._labour_generating_port1

    @property
    def labour_generating_port2(self) -> OutletPort:
        """Возвращает второй порт генерации работы"""
        return self._labour_generating_port2

    @property
    def gen_labour1(self):
        """Работа генерируемая на первый порт"""
        return self._labour_generating_port1.get()

    @gen_labour1.setter
    def gen_labour1(self, value):
        self._labour_generating_port1.set(value)

    @property
    def gen_labour2(self):
        """Работа генерируемая на второй порт"""
        return self._labour_generating_port2.get()

    @gen_labour2.setter
    def gen_labour2(self, value):
        self._labour_generating_port2.set(value)


class ConnectionSet:
    def __init__(self, connections: typing.List[ConnectionNew]):
        self.connections = connections

    def update_previous_state(self):
        for connection in self.connections:
            connection.update_previous_state()

    def get_max_residual(self):
        res = 0
        for connection in self.connections:
            if connection.get_residual() > res:
                res = connection.get_residual()
        return res


class NetworkSolverNew:
    def __init__(self, unit_arr: typing.List[UnitNew], relax_coef=1, precision=0.01, max_iter_number=50):
        self._connection_arr: typing.List[ConnectionSet] = []
        self._unit_arr = unit_arr
        self.relax_coef = relax_coef
        self.precision = precision
        self.max_iter_number = max_iter_number
        self._residual_arr = []

    def create_mechanical_connection(self, generating_unit: MechEnergyGeneratingUnit,
                                     consuming_unit1: MechEnergyConsumingUnit, consuming_unit2: MechEnergyConsumingUnit):
        """Связывает порты передачи механической энергии вырабатывающего юнита с портами приемы энергии другого юнита
        и внешней нагрузки"""
        mech_conn1 = ConnectionNew()
        mech_conn2 = ConnectionNew()
        conn_set = ConnectionSet([mech_conn1, mech_conn2])

        self._connection_arr.append(conn_set)

        generating_unit.labour_generating_port1.set_connection(mech_conn1)
        generating_unit.labour_generating_port2.set_connection(mech_conn2)
        consuming_unit2.labour_consume_port.set_connection(mech_conn2)
        consuming_unit1.labour_consume_port.set_connection(mech_conn1)

    def create_gas_dynamic_connection(self, upstream_unit: GasDynamicUnit, downstream_unit: GasDynamicUnit):
        """Связывает газодинамические порты двух юнитов"""
        temp_conn = ConnectionNew()
        pres_conn = ConnectionNew()
        alpha_conn = ConnectionNew()
        g_work_fluid_conn = ConnectionNew()
        g_fuel_conn = ConnectionNew()
        conn_set = ConnectionSet([temp_conn, pres_conn, alpha_conn, g_work_fluid_conn, g_fuel_conn])

        self._connection_arr.append(conn_set)

        upstream_unit.temp_outlet_port.set_connection(temp_conn)
        upstream_unit.pres_outlet_port.set_connection(pres_conn)
        upstream_unit.alpha_outlet_port.set_connection(alpha_conn)
        upstream_unit.g_work_fluid_outlet_port.set_connection(g_work_fluid_conn)
        upstream_unit.g_fuel_outlet_port.set_connection(g_fuel_conn)

        downstream_unit.temp_inlet_port.set_connection(temp_conn)
        downstream_unit.pres_inlet_port.set_connection(pres_conn)
        downstream_unit.alpha_inlet_port.set_connection(alpha_conn)
        downstream_unit.g_work_fluid_inlet_port.set_connection(g_work_fluid_conn)
        downstream_unit.g_fuel_inlet_port.set_connection(g_fuel_conn)

    def _set_units_behaviour(self):
        is_set = [False for _ in range(len(self._unit_arr))]
        for i in range(self.max_iter_number):
            for n, unit in enumerate(self._unit_arr):
                is_set[n] = unit.set_behaviour()
            if is_set.count(False) != 0:
                return
        raise RuntimeError('Setting of ports behaviour is not obtained')

    # TODO: реализовать инициализацию значений величин, передаваемых соединениями

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
    def _update_previous_connections_state(cls, connection_arr: typing.List[ConnectionSet]):
        for i in connection_arr:
            i.update_previous_state()

    @classmethod
    def _update_units_state(cls, unit_arr: typing.List[UnitNew], relax_coef=1):
        for i in unit_arr:
            logging.info(str(i) + ' ' + 'updating')
            i.update()
            i.update_output_connection_current_state(relax_coef)

    @classmethod
    def _get_max_residual(cls, connection_arr: typing.List[ConnectionSet]):
        result = connection_arr[0].get_max_residual()
        for i in connection_arr:
            if i.get_max_residual() > result:
                result = i.get_max_residual()
        return result

    @classmethod
    def _is_converged(cls, precision, connection_arr: typing.List[ConnectionSet]):
        def is_valid(connection_set: ConnectionSet):
            max_residual = connection_set.get_max_residual()
            return max_residual < precision

        for i in connection_arr:
            if not is_valid(i):
                return False
        return True


class Connection(metaclass=ABCMeta):
    def __init__(self):
        self._previous_state = None

    @abstractmethod
    def update_previous_state(self):
        """Создается копия текущего состояния"""
        pass

    @property
    def previous_state(self):
        return self._previous_state

    @abstractmethod
    def update_current_state(self, relax_coef):
        """
        Пересчет значений полей экземпляра класса в текущем состоянии с учетом коэффициента релаксации и
        значений полей в предыдущем состоянии
        """
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
