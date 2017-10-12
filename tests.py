import unittest
from network_lib import *
from turbine_lib import Compressor, Turbine


class NetworkElementsTests(unittest.TestCase):
    def setUp(self):
        self.upstream_gd_unit = GasDynamicUnit()
        self.downstream_gd_unit = GasDynamicUnit()
        self.mech_energy_consuming_unit1 = MechEnergyConsumingUnit()
        self.mech_energy_consuming_unit2 = MechEnergyConsumingUnit()
        self.mech_energy_generating_unit = MechEnergyGeneratingUnit()
        self.solver = NetworkSolverNew([self.upstream_gd_unit, self.downstream_gd_unit,
                                        self.mech_energy_consuming_unit1,
                                        self.mech_energy_consuming_unit2,
                                        self.mech_energy_generating_unit])
        self.solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.downstream_gd_unit)
        self.solver.create_mechanical_connection(self.mech_energy_generating_unit, self.mech_energy_consuming_unit1,
                                                 self.mech_energy_consuming_unit2)

    def test_gas_dynamic_ports_connection(self):
        """Проверка соединения газодинамических портов у соседних юнитов"""
        self.assertEqual(self.upstream_gd_unit.temp_outlet_port.get_connected_port(),
                         self.downstream_gd_unit.temp_inlet_port)
        self.assertEqual(self.upstream_gd_unit.pres_outlet_port.get_connected_port(),
                         self.downstream_gd_unit.pres_inlet_port)
        self.assertEqual(self.upstream_gd_unit.alpha_outlet_port.get_connected_port(),
                         self.downstream_gd_unit.alpha_inlet_port)
        self.assertEqual(self.upstream_gd_unit.g_work_fluid_outlet_port.get_connected_port(),
                         self.downstream_gd_unit.g_work_fluid_inlet_port)
        self.assertEqual(self.upstream_gd_unit.g_fuel_outlet_port.get_connected_port(),
                         self.downstream_gd_unit.g_fuel_inlet_port)

        self.assertEqual(self.upstream_gd_unit.temp_outlet_port,
                         self.downstream_gd_unit.temp_inlet_port.get_connected_port())
        self.assertEqual(self.upstream_gd_unit.pres_outlet_port,
                         self.downstream_gd_unit.pres_inlet_port.get_connected_port())
        self.assertEqual(self.upstream_gd_unit.alpha_outlet_port,
                         self.downstream_gd_unit.alpha_inlet_port.get_connected_port())
        self.assertEqual(self.upstream_gd_unit.g_work_fluid_outlet_port,
                         self.downstream_gd_unit.g_work_fluid_inlet_port.get_connected_port())
        self.assertEqual(self.upstream_gd_unit.g_fuel_outlet_port,
                         self.downstream_gd_unit.g_fuel_inlet_port.get_connected_port())

    def test_labour_ports_connection(self):
        """Проверка соединения портов приема и передачи работы"""
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port1.get_connected_port(),
                         self.mech_energy_consuming_unit1.labour_consume_port)
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port2.get_connected_port(),
                         self.mech_energy_consuming_unit2.labour_consume_port)

        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port1,
                         self.mech_energy_consuming_unit1.labour_consume_port.get_connected_port())
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port2,
                         self.mech_energy_consuming_unit2.labour_consume_port.get_connected_port())

    def test_information_transfer_from_upstream_to_downstream(self):
        """Проверка передача информации между соединенными портами по потоку рабочего тела или энергии"""
        self.upstream_gd_unit.temp_outlet_port.make_output()
        self.assertEqual(self.upstream_gd_unit.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.upstream_gd_unit.temp_outlet_port.get_connected_port_type(), PortType.Input)
        self.assertEqual(self.downstream_gd_unit.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.downstream_gd_unit.temp_inlet_port.get_connected_port_type(), PortType.Output)

        self.mech_energy_generating_unit.labour_generating_port1.make_input()
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port1.port_type, PortType.Input)
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port1.get_connected_port_type(),
                         PortType.Output)
        self.assertEqual(self.mech_energy_consuming_unit1.labour_consume_port.port_type, PortType.Output)
        self.assertEqual(self.mech_energy_consuming_unit1.labour_consume_port.get_connected_port_type(), PortType.Input)

    def test_information_transfer_from_downstream_to_upstream(self):
        """Проверка передача информации между соединенными портами против потока рабочего тела или энергии"""
        self.downstream_gd_unit.temp_inlet_port.make_input()
        self.assertEqual(self.upstream_gd_unit.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.upstream_gd_unit.temp_outlet_port.get_connected_port_type(), PortType.Input)
        self.assertEqual(self.downstream_gd_unit.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.downstream_gd_unit.temp_inlet_port.get_connected_port_type(), PortType.Output)

        self.mech_energy_consuming_unit1.labour_consume_port.make_output()
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port1.port_type, PortType.Input)
        self.assertEqual(self.mech_energy_generating_unit.labour_generating_port1.get_connected_port_type(),
                         PortType.Output)
        self.assertEqual(self.mech_energy_consuming_unit1.labour_consume_port.port_type, PortType.Output)
        self.assertEqual(self.mech_energy_consuming_unit1.labour_consume_port.get_connected_port_type(), PortType.Input)

    def test_exception_call(self):
        """Проверка вызова исключения при попытки присвоить неверный тип порту"""
        self.upstream_gd_unit.temp_outlet_port.make_input()
        exception_call = 0
        try:
            self.downstream_gd_unit.temp_inlet_port.make_input()
        except AssertionError:
            exception_call = 1
        self.assertEqual(exception_call, 1)

        self.upstream_gd_unit.pres_outlet_port.make_output()
        exception_call = 0
        try:
            self.downstream_gd_unit.pres_inlet_port.make_output()
        except AssertionError:
            exception_call = 1
        self.assertEqual(exception_call, 1)

        self.downstream_gd_unit.alpha_inlet_port.make_input()
        exception_call = 0
        try:
            self.upstream_gd_unit.alpha_outlet_port.make_input()
        except AssertionError:
            exception_call = 1
        self.assertEqual(exception_call, 1)

        self.downstream_gd_unit.g_fuel_inlet_port.make_output()
        exception_call = 0
        try:
            self.upstream_gd_unit.g_fuel_outlet_port.make_output()
        except AssertionError:
            exception_call = 1
        self.assertEqual(exception_call, 1)

    def test_port_information_sending_downstream(self):
        """Тестирование передачи информации через соединение по потоку"""
        outlet_port = OutletPort(self.upstream_gd_unit)
        inlet_port = InletPort(self.downstream_gd_unit)
        conn = ConnectionNew()
        outlet_port.set_connection(conn)
        inlet_port.set_connection(conn)
        outlet_port.make_output()
        self.assertEqual(PortType.Input, inlet_port.port_type)
        self.assertEqual(self.upstream_gd_unit, conn.upstream_unit)
        self.assertEqual(self.downstream_gd_unit, conn.downstream_unit)

    def test_port_information_sending_upstream(self):
        """Тестирование передачи информации через соединение против потока"""
        outlet_port = OutletPort(self.upstream_gd_unit)
        inlet_port = InletPort(self.downstream_gd_unit)
        conn = ConnectionNew()
        outlet_port.set_connection(conn)
        inlet_port.set_connection(conn)
        inlet_port.make_input()
        self.assertEqual(PortType.Output, outlet_port.port_type)


class UnitsTests(unittest.TestCase):
    def setUp(self):
        self.compressor = Compressor(5)
        self.turbine = Turbine()
        self.upstream_gd_unit = GasDynamicUnit()
        self.downstream_gd_unit = GasDynamicUnit()
        self.consume_unit1 = MechEnergyConsumingUnit()
        self.consume_unit2 = MechEnergyConsumingUnit()
        self.gen_unit = MechEnergyGeneratingUnit()

    def test_compressor_behaviour(self):
        """Проверка типов портов компрессоров"""
        solver = NetworkSolverNew([self.upstream_gd_unit, self.compressor, self.downstream_gd_unit,
                                   self.consume_unit1, self.gen_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.compressor)
        solver.create_gas_dynamic_connection(self.compressor, self.upstream_gd_unit)
        solver.create_mechanical_connection(self.gen_unit, self.compressor, self.consume_unit1)

        self.compressor.set_behaviour()

        self.assertEqual(PortType.Output, self.compressor.temp_outlet_port.port_type)
        self.assertEqual(PortType.Output, self.compressor.pres_outlet_port.port_type)
        self.assertEqual(PortType.Output, self.compressor.alpha_outlet_port.port_type)
        self.assertEqual(PortType.Output, self.compressor.g_work_fluid_outlet_port.port_type)
        self.assertEqual(PortType.Output, self.compressor.g_fuel_outlet_port.port_type)
        self.assertEqual(PortType.Output, self.compressor.labour_consume_port.port_type)

        self.assertEqual(PortType.Input, self.compressor.temp_inlet_port.port_type)
        self.assertEqual(PortType.Input, self.compressor.pres_inlet_port.port_type)
        self.assertEqual(PortType.Input, self.compressor.alpha_inlet_port.port_type)
        self.assertEqual(PortType.Input, self.compressor.g_work_fluid_inlet_port.port_type)
        self.assertEqual(PortType.Input, self.compressor.g_fuel_inlet_port.port_type)

    def test_compressor_updating(self):
        """Тестируется вызов метода update(). Проверется передача результатов расчета юнита в выходные порты"""
        solver = NetworkSolverNew([self.upstream_gd_unit, self.compressor, self.downstream_gd_unit,
                                   self.consume_unit1, self.gen_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.compressor)
        solver.create_gas_dynamic_connection(self.compressor, self.downstream_gd_unit)
        solver.create_mechanical_connection(self.gen_unit, self.compressor, self.consume_unit1)

        self.compressor.set_behaviour()
        self.upstream_gd_unit.T_stag_out = 300
        self.upstream_gd_unit.p_stag_out = 1e5
        self.upstream_gd_unit.alpha_out = np.inf
        self.upstream_gd_unit.g_fuel_out = 0
        self.upstream_gd_unit.g_out = 1

        self.compressor.update()

        self.assertEqual(self.compressor.T_stag_in, self.upstream_gd_unit.T_stag_out)
        self.assertEqual(self.compressor.p_stag_in, self.upstream_gd_unit.p_stag_out)
        self.assertEqual(self.compressor.alpha_in, self.upstream_gd_unit.alpha_out)
        self.assertEqual(self.compressor.g_in, self.upstream_gd_unit.g_out)
        self.assertEqual(self.compressor.g_fuel_in, self.upstream_gd_unit.g_fuel_out)

        self.assertNotEqual(self.compressor.consumable_labour, None)
        self.assertNotEqual(self.compressor.T_stag_out, None)
        self.assertNotEqual(self.compressor.p_stag_out, None)
        self.assertNotEqual(self.compressor.alpha_out, None)
        self.assertNotEqual(self.compressor.g_out, None)
        self.assertNotEqual(self.compressor.g_fuel_out, None)

        self.assertEqual(self.compressor.consumable_labour, self.gen_unit.gen_labour1)
        self.assertEqual(self.compressor.T_stag_out, self.downstream_gd_unit.T_stag_in)
        self.assertEqual(self.compressor.p_stag_out, self.downstream_gd_unit.p_stag_in)
        self.assertEqual(self.compressor.alpha_out, self.downstream_gd_unit.alpha_in)
        self.assertEqual(self.compressor.g_out, self.downstream_gd_unit.g_in)
        self.assertEqual(self.compressor.g_fuel_out, self.downstream_gd_unit.g_fuel_in)

    def set_turbine_connections(self):
        solver = NetworkSolverNew([self.upstream_gd_unit, self.turbine, self.downstream_gd_unit,
                                   self.consume_unit1, self.gen_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.turbine)
        solver.create_gas_dynamic_connection(self.turbine, self.downstream_gd_unit)
        solver.create_mechanical_connection(self.turbine, self.consume_unit1, self.consume_unit2)

    def test_turbine_behaviour(self):
        """Тестирует поведение портов, общее для всех типов турбин"""
        self.set_turbine_connections()
        self.turbine.set_behaviour()

        self.assertEqual(self.turbine.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.turbine.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.turbine.g_work_fluid_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.turbine.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.turbine.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.turbine.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.turbine.g_work_fluid_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.turbine.g_fuel_outlet_port.port_type, PortType.Output)

    def test_power_turbine_behaviour1(self):
        """Проверка поведения портов свободной турбины"""
        self.set_turbine_connections()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_input()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_power_turbine_behaviour())
        self.assertEqual(self.turbine.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.turbine.pres_outlet_port.port_type, PortType.Input)

    def test_power_turbine_behaviour2(self):
        """Проверка поведения портов свободной турбины"""
        self.set_turbine_connections()
        self.consume_unit1.labour_consume_port.make_input()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_power_turbine_behaviour())
        self.assertEqual(self.turbine.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.turbine.pres_outlet_port.port_type, PortType.Input)

    def test_upstream_compressor_turbine_behaviour1(self):
        """Проверка поведения портов компрессорной турбины, находящейся в газовом трактке до силовой турбины"""
        self.set_turbine_connections()
        self.upstream_gd_unit.pres_outlet_port.make_output()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_upstream_compressor_turbine_behaviour())
        self.assertEqual(self.turbine.pres_outlet_port.port_type, PortType.Output)

    def test_upstream_compressor_turbine_behaviour2(self):
        """Проверка поведения портов компрессорной турбины, находящейся в газовом трактке до силовой турбины"""
        self.set_turbine_connections()
        self.downstream_gd_unit.pres_inlet_port.make_input()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_upstream_compressor_turbine_behaviour())
        self.assertEqual(self.turbine.pres_inlet_port.port_type, PortType.Input)

    def test_downstream_compressor_turbine_behaviour1(self):
        """Проверка поведения портов компрессорной турбины, находящейся в газовом трактке после силовой турбины"""
        self.set_turbine_connections()
        self.upstream_gd_unit.pres_outlet_port.make_input()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_downstream_compressor_turbine_behaviour())
        self.assertEqual(self.turbine.pres_outlet_port.port_type, PortType.Input)

    def test_downstream_compressor_turbine_behaviour2(self):
        """Проверка поведения портов компрессорной турбины, находящейся в газовом трактке до силовой турбины"""
        self.set_turbine_connections()
        self.downstream_gd_unit.pres_inlet_port.make_output()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_downstream_compressor_turbine_behaviour())
        self.assertEqual(self.turbine.pres_inlet_port.port_type, PortType.Output)
