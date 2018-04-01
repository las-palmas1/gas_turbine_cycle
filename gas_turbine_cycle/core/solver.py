import logging

from gas_turbine_cycle.core.network_lib import *
from gas_turbine_cycle.core.turbine_lib import Compressor, Turbine, CombustionChamber, Inlet, Outlet, Load, Atmosphere, Source
from gas_turbine_cycle.gases import IdealGas, Air, KeroseneCombustionProducts

logging.basicConfig(format='%(levelname)s: %(message)s', filemode='w', filename='cycle.log', level=logging.INFO)


class NetworkSolver:
    def __init__(self, unit_arr: typing.List[Unit], relax_coef=1, precision=0.01, max_iter_number=50,
                 cold_work_fluid: IdealGas=Air(), hot_work_fluid: IdealGas=KeroseneCombustionProducts()):
        self._connection_arr: typing.List[ConnectionSet] = []
        self._unit_arr = unit_arr
        self.cold_work_fluid = cold_work_fluid
        self.hot_work_fluid = hot_work_fluid
        self.relax_coef = relax_coef
        self.precision = precision
        self.max_iter_number = max_iter_number
        self._iter_number = 0
        self._residual_arr = []

    @property
    def iter_number(self):
        return self._iter_number

    def create_mechanical_connection(self, generating_unit: MechEnergyGeneratingUnit,
                                     consuming_unit1: MechEnergyConsumingUnit, consuming_unit2: MechEnergyConsumingUnit):
        """Связывает порты передачи механической энергии вырабатывающего юнита с портами приемы энергии другого юнита
        и внешней нагрузки"""
        assert (self._unit_arr.count(generating_unit) != 0 and self._unit_arr.count(consuming_unit1) != 0 and
                self._unit_arr.count(consuming_unit2) != 0), \
            "You try to connect units, of which at least one isn't added to the solver units list."
        mech_conn1 = Connection()
        mech_conn2 = Connection()
        conn_set = ConnectionSet([mech_conn1, mech_conn2])

        self._connection_arr.append(conn_set)

        generating_unit.labour_generating_port1.set_connection(mech_conn1)
        generating_unit.labour_generating_port2.set_connection(mech_conn2)
        consuming_unit2.labour_consume_port.set_connection(mech_conn2)
        consuming_unit1.labour_consume_port.set_connection(mech_conn1)

    def create_gas_dynamic_connection(self, upstream_unit: GasDynamicUnit, downstream_unit: GasDynamicUnit):
        """Связывает газодинамические порты двух юнитов"""
        assert self._unit_arr.count(upstream_unit) != 0 and self._unit_arr.count(downstream_unit) != 0, \
            "You try to connect units, of which at least one isn't added to the solver units list."
        temp_conn = Connection()
        pres_conn = Connection()
        alpha_conn = Connection()
        g_work_fluid_conn = Connection()
        g_fuel_conn = Connection()
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

    def create_static_gas_dynamic_connection(self, upstream_unit: GasDynamicUnitStaticOutlet,
                                             downstream_unit: GasDynamicUnitStaticInlet):
        """Связывает газодинамические порты двух юнитов со статическим выходом и входом."""
        assert self._unit_arr.count(upstream_unit) != 0 and self._unit_arr.count(downstream_unit) != 0, \
            "You try to connect units, of which at least one isn't added to the solver units list."
        temp_conn = Connection()
        pres_conn = Connection()
        stat_temp_conn = Connection()
        stat_pres_conn = Connection()
        alpha_conn = Connection()
        g_work_fluid_conn = Connection()
        g_fuel_conn = Connection()
        conn_set = ConnectionSet([temp_conn, pres_conn, stat_temp_conn, stat_pres_conn, alpha_conn,
                                  g_work_fluid_conn, g_fuel_conn])

        self._connection_arr.append(conn_set)

        upstream_unit.temp_outlet_port.set_connection(temp_conn)
        upstream_unit.pres_outlet_port.set_connection(pres_conn)
        upstream_unit.alpha_outlet_port.set_connection(alpha_conn)
        upstream_unit.g_work_fluid_outlet_port.set_connection(g_work_fluid_conn)
        upstream_unit.g_fuel_outlet_port.set_connection(g_fuel_conn)
        upstream_unit.stat_temp_outlet_port.set_connection(stat_temp_conn)
        upstream_unit.stat_pres_outlet_port.set_connection(stat_pres_conn)

        downstream_unit.temp_inlet_port.set_connection(temp_conn)
        downstream_unit.pres_inlet_port.set_connection(pres_conn)
        downstream_unit.alpha_inlet_port.set_connection(alpha_conn)
        downstream_unit.g_work_fluid_inlet_port.set_connection(g_work_fluid_conn)
        downstream_unit.g_fuel_inlet_port.set_connection(g_fuel_conn)
        downstream_unit.stat_temp_inlet_port.set_connection(stat_temp_conn)
        downstream_unit.stat_pres_inlet_port.set_connection(stat_pres_conn)

    def get_sorted_unit_list(self) -> typing.List[Unit]:
        """Возвращает отсортированный список юнитов, в котором снала следуют газодинамические юниты
        в порядке протекания через них рабочего тела, затем нагрузки"""
        res = []
        for unit in self._unit_arr:
            if type(unit) == Atmosphere:
                res.append(unit)
        unit = res[0].get_downstream_unit()
        while type(unit) != Atmosphere:
            res.append(unit)
            unit = unit.get_downstream_unit()
        for unit in self._unit_arr:
            if type(unit) == Load:
                res.append(unit)
        return res

    def set_units_behaviour(self):
        logging.info('Start behaviour setting')
        is_set = [False for _ in range(len(self._unit_arr))]
        for i in range(self.max_iter_number):
            logging.info('Iteration %s' % (i + 1))
            for n, unit in enumerate(self._unit_arr):
                unit.set_behaviour()
                is_set[n] = unit.has_undefined_ports()
            if is_set.count(True) == 0:
                logging.info('End behaviour setting\n')
                return
        raise RuntimeError('Setting of ports behaviour is not obtained')

    def solve(self):
        self.set_units_behaviour()
        sorted_units_list = self.get_sorted_unit_list()
        self.set_work_fluid(sorted_units_list)
        for i in range(self.max_iter_number):
            self._iter_number = i + 1
            logging.info('Iteration %s\n' % i)
            self._update_previous_connections_state(self._connection_arr)
            self._update_units_state(sorted_units_list, self.relax_coef)
            self._residual_arr.append(self._get_max_residual(self._connection_arr))
            logging.info('MAX RESIDUAL = %.4f\n' % (self._get_max_residual(self._connection_arr)))
            if self._is_converged(self.precision, self._connection_arr):
                return
        raise RuntimeError('Convergence is not obtained')

    @classmethod
    def _update_previous_connections_state(cls, connection_arr: typing.List[ConnectionSet]):
        for i in connection_arr:
            i.update_previous_state()

    def set_work_fluid(self, unit_list: typing.List[Unit]):
        """
        :param unit_list: отсортированный список юнитов
        :return:
        """
        for unit in unit_list:
            if type(unit) == Inlet or type(unit) == Compressor:
                unit.work_fluid = type(self.cold_work_fluid)()
            elif type(unit) == Outlet or type(unit) == Turbine:
                unit.work_fluid = type(self.hot_work_fluid)()
            elif type(unit) == Atmosphere:
                unit.work_fluid_in = type(self.hot_work_fluid)()
                unit.work_fluid_out = type(self.cold_work_fluid)()
            elif type(unit) == Source:
                unit.work_fluid = type(self.hot_work_fluid)()
                unit.return_fluid = type(self.cold_work_fluid)()
        count = 0
        for unit in unit_list:
            if type(unit) == CombustionChamber:
                count += 1
                if count == 1:
                    unit.work_fluid_in = type(self.cold_work_fluid)()
                    unit.work_fluid_out = type(self.hot_work_fluid)()
                    unit.work_fluid_out_T0 = type(self.hot_work_fluid)()
                else:
                    unit.work_fluid_in = type(self.hot_work_fluid)()
                    unit.work_fluid_out = type(self.hot_work_fluid)()
                    unit.work_fluid_out_T0 = type(self.hot_work_fluid)()

    @classmethod
    def _update_units_state(cls, sorted_unit_list: typing.List[Unit], relax_coef=1):
        for i in sorted_unit_list:
            if type(i) == Load:
                i.update()
        for i in sorted_unit_list:
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

