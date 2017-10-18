from abc import ABCMeta, abstractmethod
import enum
import typing


class Unit:
    def __init__(self):
        self.input_ports: typing.List[Port] = []
        "Список входных портов"
        self.output_ports: typing.List[Port] = []
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

    def set_behaviour(self):
        """
        :return: None
        Настойка типов всех портов.
        """
        pass

    def has_undefined_ports(self) -> bool:
        """
        :return: True, если есть порты с неопределенным типом, False - в противном случае
        Проверка наличия портов с типом PortType.Undefined
        """
        for key in self.__dict__:
            if key.count('port') == 1 and key.count('ports') == 0:
                if self.__dict__[key].port_type == PortType.Undefined:
                    return True
        return False

    def check_input(self) -> bool:
        """Производит проверку исходных для расчета юнита параметров. Возвращает False, если хотя
        бы один из них равен None"""
        pass


class PortType(enum.Enum):
    """Тип порта"""
    Input = 0
    "Порт осуществляет доступ к входным для расчета юнита данным. Порт не может принимать значение"
    Output = 1
    "Порт осуществляет доступ к выходным данным. Порт может принимать значение"
    Undefined = 2


class Connection:
    """Класс соединяющий порты"""
    def __init__(self):
        self.value = None
        "Значение передаваемого параметра"
        self.upstream_port: OutletPort = None
        "Порт следующего по течению или направлению передачи работы юнита"
        self.downstream_port: InletPort = None
        "Порт предыдущего по течению или направлению передачи работы юнита"
        self.upstream_unit: Unit = None
        "Следующий по течению или направлению передачи работы юнит"
        self.downstream_unit: Unit = None
        "Предыдущий по течению или направлению передачи работы юнит"
        self.previous_value = None
        "Значение передаваемого параметра в предыдущем состоянии"

    def update_previous_state(self):
        self.previous_value = self.value

    def get_residual(self):
        """Возврат значения невязки"""
        if self.value is not None and self.previous_value is not None and self.value != 0 and self.previous_value != 0:
            return abs(self.value - self.previous_value) / self.value
        elif self.value is not None and self.previous_value is not None and self.value == 0 \
                and self.previous_value == 0:
            return 0
        else:
            return 1

    def update_current_state(self, relax_coef=1):
        """Пересчитывает текущее значение с учетом релаксации"""
        if self.value is not None and self.previous_value is not None:
            self.value = self.previous_value + relax_coef * (self.value - self.previous_value)


class Port(metaclass=ABCMeta):
    """Класс, через который из юнитов можно осуществлять доступ к связям (Connection)"""
    def __init__(self, unit: Unit):
        self._unit = unit
        self.value = None
        "Копия значения, хранимого в соединении"
        self._linked_connection: Connection = None
        self._port_type: PortType = PortType.Undefined

    @property
    def unit(self) -> Unit:
        """Юнит, которому принадлежит порт"""
        return self._unit

    def get(self):
        """Возвращает хранимое в соединении значении"""
        return self._linked_connection.value

    def set(self, value):
        """Задает хранимое в соединении значении"""
        assert self._port_type == PortType.Output, "You can't set value of parameter in Connection " \
                                                   "object via this port in this unit because it's not output port"
        self.value = value
        self._linked_connection.value = value

    @abstractmethod
    def set_connection(self, connection: Connection):
        """Задание соединение, к которому через порт можно осуществить доступ"""
        pass

    def update_connection_current_state(self, relax_coef=1):
        """Обновляет текущее состояние соединения с учетом коэффициента релаксации"""
        self._linked_connection.update_current_state(relax_coef=relax_coef)

    def make_input(self):
        """Меняет тип порта на Input"""
        self._port_type = PortType.Input
        assert self.get_connected_port_type() != PortType.Input, 'Connected port must not have the same type: %s' % \
                                                                 PortType.Input
        if self.get_connected_port_type() == PortType.Undefined:
            self.get_connected_port().make_output()

    def make_output(self):
        """Меняет тип порта на Output"""
        self._port_type = PortType.Output
        assert self.get_connected_port_type() != PortType.Output, 'Connected port must not have the same type: %s' % \
                                                                  PortType.Output
        if self.get_connected_port_type() == PortType.Undefined:
            self.get_connected_port().make_input()

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


class OutletPort(Port):
    """Порт, соответствующий газодинамическому или энергетическому выходу юнита"""
    def __init__(self, unit: Unit):
        Port.__init__(self, unit)

    def get_connected_port(self):
        assert self._linked_connection is not None, "Port hasn't been connected with another port yet."
        return self._linked_connection.downstream_port

    def get_connected_port_type(self) -> PortType:
        assert self._linked_connection is not None, "Port hasn't been connected with another port yet."
        return self._linked_connection.downstream_port.port_type

    def set_connection(self, connection: Connection):
        if self.value:
            connection.value = self.value
        self._linked_connection = connection
        self._linked_connection.upstream_port = self
        self._linked_connection.upstream_unit = self._unit


class InletPort(Port):
    """Порт, соответствующий газодинамическому или энергетическому входу юнита"""
    def __init__(self, unit: Unit):
        Port.__init__(self, unit)

    def get_connected_port(self):
        assert self._linked_connection is not None, "Port hasn't been connected with another port yet."
        return self._linked_connection.upstream_port

    def get_connected_port_type(self) -> PortType:
        assert self._linked_connection is not None, "Port hasn't been connected with another port yet."
        return self._linked_connection.upstream_port.port_type

    def set_connection(self, connection: Connection):
        if self.value:
            connection.value = self.value
        self._linked_connection = connection
        self._linked_connection.downstream_port = self
        self._linked_connection.downstream_unit = self._unit


class GasDynamicUnit(Unit):
    """Инициализирует и осуществляет доступ к газодинамическим портам"""
    def __init__(self):
        Unit.__init__(self)
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

    def get_upstream_unit(self):
        """Возвращает юнит, находящийся выше по течению"""
        return self.temp_inlet_port.get_connected_port().unit

    def get_downstream_unit(self):
        """Возвращает юнит, находящийся ниже по течению"""
        return self.temp_outlet_port.get_connected_port().unit

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
        """Относительный расход топлива на входе, равный сумме относительных расходов
        во всех предшествующих по газовому тракту камерах сгорания (NOTE: в к.с. он определяется как
        отношение расхода топлива к расходу рабочего тела на входе)"""
        return self._g_fuel_inlet_port.get()

    @g_fuel_in.setter
    def g_fuel_in(self, value):
        self._g_fuel_inlet_port.set(value)

    @property
    def g_in(self):
        """Суммарный относительный расход рабочего тела на входе."""
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
        """Суммарный относительный расход топлива на выходе, равный сумме относительных расходов
        во всех предшествующих по газовому тракту камерах сгорания и текущем юните(NOTE: в к.с. он определяется как
        отношение расхода топлива к расходу рабочего тела на входе)"""
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


class MechEnergyConsumingUnit(Unit):
    """Осуществляет доступ к портам приема работы юнита, потребляющего механическую энергию"""
    def __init__(self):
        Unit.__init__(self)
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


class MechEnergyGeneratingUnit(Unit):
    """Осуществляет доступ к портам отдачи работы юнита, генерирующего механическую энергию"""
    def __init__(self):
        Unit.__init__(self)
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
    def __init__(self, connections: typing.List[Connection]):
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

