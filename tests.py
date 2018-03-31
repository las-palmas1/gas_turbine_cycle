import logging
import unittest

import numpy as np

from gas_turbine_cycle.core.network_lib import *
from gas_turbine_cycle.core.solver import NetworkSolver
from gas_turbine_cycle.core.turbine_lib import Compressor, Turbine, Source, Sink, CombustionChamber, Inlet, Outlet, \
    Atmosphere, Load, FullExtensionNozzle
from gas_turbine_cycle.gases import KeroseneCombustionProducts, NaturalGasCombustionProducts, Air

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


class NetworkElementsTests(unittest.TestCase):
    def setUp(self):
        self.upstream_gd_unit = GasDynamicUnit()
        self.downstream_gd_unit = GasDynamicUnit()
        self.mech_energy_consuming_unit1 = MechEnergyConsumingUnit()
        self.mech_energy_consuming_unit2 = MechEnergyConsumingUnit()
        self.mech_energy_generating_unit = MechEnergyGeneratingUnit()
        self.solver = NetworkSolver([self.upstream_gd_unit, self.downstream_gd_unit,
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
        conn = Connection()
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
        conn = Connection()
        outlet_port.set_connection(conn)
        inlet_port.set_connection(conn)
        inlet_port.make_input()
        self.assertEqual(PortType.Output, outlet_port.port_type)


class UnitsTests(unittest.TestCase):
    def setUp(self):
        self.inlet = Inlet()
        self.atmosphere = Atmosphere(lam_in=0.1)
        self.outlet = Outlet()
        self.comb_chamber = CombustionChamber(1450, p_stag_out_init=10e5, alpha_out_init=2.4)
        self.compressor = Compressor(5)
        self.turbine = Turbine(p_stag_out_init=1e5)
        self.source = Source(work_fluid=KeroseneCombustionProducts(), g_return=0.05, return_fluid_temp=700)
        self.sink = Sink()
        self.nozzle = FullExtensionNozzle()
        self.upstream_gd_unit = GasDynamicUnit()
        self.upstream_static_gd_unit = GasDynamicUnitStaticOutlet()
        self.downstream_gd_unit = GasDynamicUnit()
        self.downstream_static_gd_unit = GasDynamicUnitStaticInlet()
        self.consume_unit1 = MechEnergyConsumingUnit()
        self.consume_unit2 = MechEnergyConsumingUnit()
        self.gen_unit = MechEnergyGeneratingUnit()

    def test_compressor_behaviour(self):
        """Проверка типов портов компрессоров"""
        solver = NetworkSolver([self.upstream_gd_unit, self.compressor, self.downstream_gd_unit,
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
        solver = NetworkSolver([self.upstream_gd_unit, self.compressor, self.downstream_gd_unit,
                                self.consume_unit1, self.gen_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.compressor)
        solver.create_gas_dynamic_connection(self.compressor, self.downstream_gd_unit)
        solver.create_mechanical_connection(self.gen_unit, self.compressor, self.consume_unit1)
        self.compressor.set_behaviour()

        self.assertFalse(self.compressor.check_input())
        self.upstream_gd_unit.T_stag_out = 300
        self.assertFalse(self.compressor.check_input())
        self.upstream_gd_unit.p_stag_out = 1e5
        self.assertFalse(self.compressor.check_input())
        self.upstream_gd_unit.alpha_out = np.inf
        self.assertFalse(self.compressor.check_input())
        self.upstream_gd_unit.g_fuel_out = 0
        self.assertFalse(self.compressor.check_input())
        self.upstream_gd_unit.g_out = 1

        self.assertTrue(self.compressor.check_input())

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
        solver = NetworkSolver([self.upstream_gd_unit, self.turbine, self.downstream_gd_unit,
                                self.consume_unit1, self.gen_unit, self.consume_unit2])
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
        """Проверка поведения портов компрессорной турбины, находящейся в газовом тракте после силовой турбины"""
        self.set_turbine_connections()
        self.upstream_gd_unit.pres_outlet_port.make_input()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_downstream_compressor_turbine_behaviour())
        self.assertEqual(self.turbine.pres_outlet_port.port_type, PortType.Input)

    def test_downstream_compressor_turbine_behaviour2(self):
        """Проверка поведения портов компрессорной турбины, находящейся в газовом тракте до силовой турбины"""
        self.set_turbine_connections()
        self.downstream_gd_unit.pres_inlet_port.make_output()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertTrue(self.turbine.check_downstream_compressor_turbine_behaviour())
        self.assertEqual(self.turbine.pres_inlet_port.port_type, PortType.Output)

    def test_power_turbine_updating(self):
        self.set_turbine_connections()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_input()
        self.turbine.set_behaviour()

        self.assertFalse(self.turbine.check_input())
        self.consume_unit1.consumable_labour = 200e3
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.T_stag_out = 1400
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.p_stag_out = 10e5
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.g_fuel_out = 0.05
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.g_out = 1.04
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.alpha_out = 2.5
        self.assertTrue(self.turbine.check_input())
        self.downstream_gd_unit.p_stag_in = 3.5e5
        self.assertTrue(self.turbine.check_input())

        self.turbine.update()

        print()
        print('Power turbine testing')
        print('T_stag_out = %.2f' % self.turbine.T_stag_out)
        print('alpha_out = %.3f' % self.turbine.alpha_out)
        print('g_fuel_out = %.3f' % self.turbine.g_fuel_out)
        print('g_out = %.3f' % self.turbine.g_out)
        print('gen_labour2 = %s' % round(self.turbine.gen_labour2, -3))
        self.assertNotEqual(self.turbine.T_stag_out, None)
        self.assertNotEqual(self.turbine.alpha_out, None)
        self.assertNotEqual(self.turbine.g_fuel_out, None)
        self.assertNotEqual(self.turbine.g_out, None)
        self.assertNotEqual(self.turbine.gen_labour2, None)
        # проверка баланса работ
        self.assertAlmostEqual(self.turbine.total_labour * self.turbine.g_in * self.turbine.eta_m,
                               self.consume_unit1.consumable_labour +
                               self.consume_unit2.consumable_labour / self.turbine.eta_r,
                               places=3)

    def test_upstream_compressor_turbine_updating(self):
        self.set_turbine_connections()
        self.upstream_gd_unit.pres_outlet_port.make_output()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertFalse(self.turbine.check_input())
        self.consume_unit1.consumable_labour = 200e3
        self.assertFalse(self.turbine.check_input())
        self.consume_unit2.consumable_labour = 0
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.T_stag_out = 1400
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.p_stag_out = 10e5
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.g_fuel_out = 0.05
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.g_out = 1.04
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.alpha_out = 2.5
        self.assertTrue(self.turbine.check_input())
        self.turbine.update()

        print()
        print('Upstream compressor turbine testing')
        print('T_stag_out = %.2f' % self.turbine.T_stag_out)
        print('alpha_out = %.3f' % self.turbine.alpha_out)
        print('g_fuel_out = %.3f' % self.turbine.g_fuel_out)
        print('g_out = %.3f' % self.turbine.g_out)
        print('p_stag_out = %s' % round(self.turbine.p_stag_out, -3))
        self.assertNotEqual(self.turbine.T_stag_out, None)
        self.assertNotEqual(self.turbine.alpha_out, None)
        self.assertNotEqual(self.turbine.g_fuel_out, None)
        self.assertNotEqual(self.turbine.g_out, None)
        self.assertNotEqual(self.turbine.p_stag_out, None)
        # проверка баланса работ
        self.assertAlmostEqual(self.turbine.total_labour * self.turbine.g_in * self.turbine.eta_m,
                               self.consume_unit1.consumable_labour + self.consume_unit2.consumable_labour, places=2)

    def test_downstream_compressor_turbine_updating(self):
        self.set_turbine_connections()
        self.downstream_gd_unit.pres_inlet_port.make_output()
        self.consume_unit1.labour_consume_port.make_output()
        self.consume_unit2.labour_consume_port.make_output()
        self.turbine.set_behaviour()

        self.assertFalse(self.turbine.check_input())
        self.consume_unit1.consumable_labour = 200e3
        self.assertFalse(self.turbine.check_input())
        self.consume_unit2.consumable_labour = 0
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.T_stag_out = 1400
        self.assertFalse(self.turbine.check_input())
        self.downstream_gd_unit.p_stag_in = 6e5
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.g_fuel_out = 0.05
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.g_out = 1.04
        self.assertFalse(self.turbine.check_input())
        self.upstream_gd_unit.alpha_out = 2.5
        self.assertTrue(self.turbine.check_input())
        self.turbine.update()

        print()
        print('Downstream compressor turbine testing')
        print('T_stag_out = %.2f' % self.turbine.T_stag_out)
        print('alpha_out = %.3f' % self.turbine.alpha_out)
        print('g_fuel_out = %.3f' % self.turbine.g_fuel_out)
        print('g_out = %.3f' % self.turbine.g_out)
        print('p_stag_in = %s' % round(self.turbine.p_stag_in, -3))
        self.assertNotEqual(self.turbine.T_stag_out, None)
        self.assertNotEqual(self.turbine.alpha_out, None)
        self.assertNotEqual(self.turbine.g_fuel_out, None)
        self.assertNotEqual(self.turbine.g_out, None)
        self.assertNotEqual(self.turbine.p_stag_in, None)
        # проверка баланса работ
        self.assertAlmostEqual(self.turbine.total_labour * self.turbine.g_in * self.turbine.eta_m,
                               self.consume_unit1.consumable_labour + self.consume_unit2.consumable_labour, places=2)

    def test_upstream_source(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.source, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.source)
        solver.create_gas_dynamic_connection(self.source, self.downstream_gd_unit)

        self.upstream_gd_unit.pres_outlet_port.make_output()
        self.source.set_behaviour()

        g_fuel = 0.04
        g = 1.04
        alpha = 1 / (self.source.work_fluid.l0 * (g_fuel / (g - g_fuel)))
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.T_stag_out = 1200
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.p_stag_out = 2.5e5
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.g_out = g
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.g_fuel_out = g_fuel
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.alpha_out = alpha
        self.assertTrue(self.source.check_input())
        self.source.update()

        self.assertTrue(self.source.check_upstream_behaviour())
        self.assertEqual(self.source.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.source.pres_outlet_port.port_type, PortType.Output)
        self.assertNotEqual(self.source.g_out, None)
        self.assertNotEqual(self.source.g_fuel_out, None)
        self.assertNotEqual(self.source.alpha_out, None)
        self.assertNotEqual(self.source.p_stag_out, None)
        self.assertNotEqual(self.source.T_stag_out, None)
        self.assertEqual(self.source.g_out, self.source.g_in + self.source.g_return)
        self.assertLess(self.source.T_stag_out, self.source.T_stag_in)
        self.assertGreater(self.source.alpha_out, self.source.alpha_in)

    def test_downstream_source(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.source, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.source)
        solver.create_gas_dynamic_connection(self.source, self.downstream_gd_unit)

        self.upstream_gd_unit.pres_outlet_port.make_input()
        self.source.set_behaviour()

        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.T_stag_out = 500
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.alpha_out = 2.5
        self.assertFalse(self.source.check_input())
        self.downstream_gd_unit.p_stag_in = 2.5e5
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.g_out = 1.04
        self.assertFalse(self.source.check_input())
        self.upstream_gd_unit.g_fuel_out = 0.04
        self.assertTrue(self.source.check_input())
        self.source.update()

        self.assertTrue(self.source.check_downstream_behaviour())
        self.assertEqual(self.source.pres_inlet_port.port_type, PortType.Output)
        self.assertEqual(self.source.pres_outlet_port.port_type, PortType.Input)
        self.assertNotEqual(self.source.g_out, None)
        self.assertNotEqual(self.source.g_fuel_out, None)
        self.assertNotEqual(self.source.alpha_out, None)
        self.assertNotEqual(self.source.p_stag_in, None)
        self.assertNotEqual(self.source.T_stag_out, None)
        self.assertEqual(self.source.g_out, self.source.g_in + self.source.g_return)

    def test_sink(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.sink, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.sink)
        solver.create_gas_dynamic_connection(self.sink, self.downstream_gd_unit)

        self.sink.set_behaviour()
        self.assertEqual(self.sink.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.sink.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.sink.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.sink.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.sink.g_work_fluid_inlet_port.port_type, PortType.Input)

        self.assertEqual(self.sink.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.sink.pres_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.sink.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.sink.g_fuel_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.sink.g_work_fluid_outlet_port.port_type, PortType.Output)

        self.assertFalse(self.sink.check_input())
        self.upstream_gd_unit.T_stag_out = 500
        self.assertFalse(self.sink.check_input())
        self.upstream_gd_unit.alpha_out = 2.5
        self.assertFalse(self.sink.check_input())
        self.upstream_gd_unit.p_stag_out = 2.5e5
        self.assertFalse(self.sink.check_input())
        self.upstream_gd_unit.g_out = 1.04
        self.assertFalse(self.sink.check_input())
        self.upstream_gd_unit.g_fuel_out = 0.04
        self.assertTrue(self.sink.check_input())
        self.sink.update()

        self.assertNotEqual(self.sink.T_stag_out, None)
        self.assertNotEqual(self.sink.p_stag_out, None)
        self.assertNotEqual(self.sink.alpha_out, None)
        self.assertNotEqual(self.sink.g_out, None)
        self.assertNotEqual(self.sink.g_fuel_out, None)
        self.assertEqual(self.sink.g_out, self.sink.g_in - self.sink.g_cooling - self.sink.g_outflow)

    def test_upstream_combustion_chamber(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.comb_chamber, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.downstream_gd_unit)

        self.upstream_gd_unit.pres_outlet_port.make_output()
        self.comb_chamber.set_behaviour()

        self.assertEqual(self.comb_chamber.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.g_work_fluid_inlet_port.port_type, PortType.Input)

        self.assertEqual(self.comb_chamber.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.pres_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.g_fuel_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.g_work_fluid_outlet_port.port_type, PortType.Output)

        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.T_stag_out = 700
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.p_stag_out = 10e5
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.alpha_out = np.inf
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.g_fuel_out = 0
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.g_out = 0.95
        self.assertTrue(self.comb_chamber.check_input())

        self.comb_chamber.update()
        print()
        print('Upstream combustion chamber testing')
        print('T_stag_out = %.2f' % self.comb_chamber.T_stag_out)
        print('p_stag_out = %s' % round(self.comb_chamber.p_stag_out, -2))
        print('alpha_res = %.3f' % self.comb_chamber.alpha_res)
        print('alpha_out = %.3f' % self.comb_chamber.alpha_out)
        print('g_fuel_prime = %.4f' % self.comb_chamber.g_fuel_prime)
        print('g_fuel_out = %.4f' % self.comb_chamber.g_fuel_out)
        print('g_out = %.4f' % self.comb_chamber.g_out)

        self.assertNotEqual(self.comb_chamber.T_stag_out, None)
        self.assertNotEqual(self.comb_chamber.p_stag_out, None)
        self.assertNotEqual(self.comb_chamber.g_out, None)
        self.assertNotEqual(self.comb_chamber.g_fuel_out, None)
        self.assertEqual(self.comb_chamber.g_out, self.comb_chamber.g_in * (1 + self.comb_chamber.g_fuel_prime))

    def test_downstream_combustion_chamber(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.comb_chamber, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.downstream_gd_unit)

        self.downstream_gd_unit.pres_inlet_port.make_output()
        self.comb_chamber.set_behaviour()

        self.assertEqual(self.comb_chamber.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.pres_inlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.g_work_fluid_inlet_port.port_type, PortType.Input)

        self.assertEqual(self.comb_chamber.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.pres_outlet_port.port_type, PortType.Input)
        self.assertEqual(self.comb_chamber.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.g_fuel_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.comb_chamber.g_work_fluid_outlet_port.port_type, PortType.Output)

        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.T_stag_out = 700
        self.assertFalse(self.comb_chamber.check_input())
        self.downstream_gd_unit.p_stag_in = 10e5
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.alpha_out = np.inf
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.g_fuel_out = 0
        self.assertFalse(self.comb_chamber.check_input())
        self.upstream_gd_unit.g_out = 0.95
        self.assertTrue(self.comb_chamber.check_input())

        self.comb_chamber.update()
        print()
        print('Downstream combustion chamber testing')
        print('T_stag_out = %.2f' % self.comb_chamber.T_stag_out)
        print('p_stag_in = %s' % round(self.comb_chamber.p_stag_in, -2))
        print('alpha_res = %.3f' % self.comb_chamber.alpha_res)
        print('alpha_out = %.3f' % self.comb_chamber.alpha_out)
        print('g_fuel_prime = %.4f' % self.comb_chamber.g_fuel_prime)
        print('g_fuel_out = %.4f' % self.comb_chamber.g_fuel_out)
        print('g_out = %.4f' % self.comb_chamber.g_out)

        self.assertNotEqual(self.comb_chamber.T_stag_out, None)
        self.assertNotEqual(self.comb_chamber.p_stag_in, None)
        self.assertNotEqual(self.comb_chamber.g_out, None)
        self.assertNotEqual(self.comb_chamber.g_fuel_out, None)
        self.assertEqual(self.comb_chamber.g_out, self.comb_chamber.g_in * (1 + self.comb_chamber.g_fuel_prime))

    def test_inlet(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.inlet, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.inlet)
        solver.create_gas_dynamic_connection(self.inlet, self.downstream_gd_unit)

        self.inlet.set_behaviour()

        self.assertEqual(self.inlet.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.inlet.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.inlet.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.inlet.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.inlet.g_work_fluid_inlet_port.port_type, PortType.Input)

        self.assertEqual(self.inlet.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.inlet.pres_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.inlet.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.inlet.g_fuel_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.inlet.g_work_fluid_outlet_port.port_type, PortType.Output)

        self.assertFalse(self.inlet.check_input())
        self.upstream_gd_unit.T_stag_out = 300
        self.assertFalse(self.inlet.check_input())
        self.upstream_gd_unit.p_stag_out = 1e5
        self.assertFalse(self.inlet.check_input())
        self.upstream_gd_unit.alpha_out = np.inf
        self.assertFalse(self.inlet.check_input())
        self.upstream_gd_unit.g_fuel_out = 0
        self.assertFalse(self.inlet.check_input())
        self.upstream_gd_unit.g_out = 1.0
        self.assertTrue(self.inlet.check_input())

        self.inlet.update()
        self.assertNotEqual(self.inlet.T_stag_out, None)
        self.assertNotEqual(self.inlet.p_stag_out, None)
        self.assertNotEqual(self.inlet.alpha_out, None)
        self.assertNotEqual(self.inlet.g_fuel_out, None)
        self.assertNotEqual(self.inlet.g_out, None)
        self.assertEqual(self.inlet.p_stag_out, self.inlet.p_stag_in * self.inlet.sigma)

    def test_outlet(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.outlet, self.downstream_static_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.outlet)
        solver.create_static_gas_dynamic_connection(self.outlet, self.downstream_static_gd_unit)

        self.outlet.set_behaviour()

        self.assertEqual(self.outlet.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.outlet.pres_inlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.outlet.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.outlet.g_work_fluid_inlet_port.port_type, PortType.Input)

        self.assertEqual(self.outlet.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.pres_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.g_fuel_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.g_work_fluid_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.stat_temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.outlet.stat_pres_outlet_port.port_type, PortType.Input)

        self.assertFalse(self.outlet.check_input())
        self.upstream_gd_unit.T_stag_out = 300
        self.assertFalse(self.outlet.check_input())
        self.upstream_gd_unit.alpha_out = np.inf
        self.assertFalse(self.outlet.check_input())
        self.upstream_gd_unit.g_fuel_out = 0
        self.assertFalse(self.outlet.check_input())
        self.upstream_gd_unit.g_out = 1.0
        self.assertFalse(self.outlet.check_input())
        self.downstream_static_gd_unit.p_in = 1e5
        self.assertTrue(self.outlet.check_input())

        self.outlet.update()
        self.assertNotEqual(self.outlet.T_stag_out, None)
        self.assertNotEqual(self.outlet.p_stag_in, None)
        self.assertNotEqual(self.outlet.alpha_out, None)
        self.assertNotEqual(self.outlet.g_fuel_out, None)
        self.assertNotEqual(self.outlet.g_out, None)
        self.assertEqual(self.outlet.p_stag_in, self.outlet.p_stag_out / self.outlet.sigma)

    def test_nozzle(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.nozzle, self.downstream_static_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.nozzle)
        solver.create_static_gas_dynamic_connection(self.nozzle, self.downstream_static_gd_unit)

        self.nozzle.set_behaviour()

        self.assertEqual(self.nozzle.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.nozzle.pres_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.nozzle.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.nozzle.g_work_fluid_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.nozzle.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.nozzle.stat_pres_outlet_port.port_type, PortType.Input)

        self.assertEqual(self.nozzle.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.nozzle.pres_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.nozzle.stat_temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.nozzle.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.nozzle.g_work_fluid_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.nozzle.g_fuel_outlet_port.port_type, PortType.Output)

        self.upstream_gd_unit.g_fuel_out = 0.02
        self.upstream_gd_unit.g_out = 1.02
        self.upstream_gd_unit.alpha_out = 2.5
        self.upstream_gd_unit.T_stag_out = 1000
        self.upstream_gd_unit.p_stag_out = 2.5e5
        self.downstream_static_gd_unit.p_in = 1.e5

        self.nozzle.update()

        self.assertNotEqual(self.nozzle.T_out, None)
        self.assertNotEqual(self.nozzle.T_stag_out, None)
        self.assertNotEqual(self.nozzle.p_stag_out, None)
        self.assertNotEqual(self.nozzle.pi_n, None)
        self.assertNotEqual(self.nozzle.H_n, None)
        self.assertNotEqual(self.nozzle.c_out, None)
        self.assertNotEqual(self.nozzle.alpha_out, None)
        self.assertNotEqual(self.nozzle.g_out, None)
        self.assertNotEqual(self.nozzle.g_fuel_out, None)

    def test_atmosphere(self):
        solver = NetworkSolver([self.upstream_static_gd_unit, self.atmosphere, self.downstream_gd_unit])
        solver.create_static_gas_dynamic_connection(self.upstream_static_gd_unit, self.atmosphere)
        solver.create_gas_dynamic_connection(self.atmosphere, self.downstream_gd_unit)

        self.atmosphere.set_behaviour()
        self.assertEqual(self.atmosphere.temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.atmosphere.alpha_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.atmosphere.g_fuel_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.atmosphere.g_work_fluid_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.atmosphere.stat_temp_inlet_port.port_type, PortType.Input)
        self.assertEqual(self.atmosphere.pres_inlet_port.port_type, PortType.Input)

        self.assertEqual(self.atmosphere.temp_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.atmosphere.pres_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.atmosphere.stat_pres_inlet_port.port_type, PortType.Output)
        self.assertEqual(self.atmosphere.alpha_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.atmosphere.g_fuel_outlet_port.port_type, PortType.Output)
        self.assertEqual(self.atmosphere.g_work_fluid_outlet_port.port_type, PortType.Output)

        self.upstream_static_gd_unit.T_stag_out = 500
        self.upstream_static_gd_unit.alpha_out = 2.5
        self.upstream_static_gd_unit.g_fuel_out = 0.05
        self.upstream_static_gd_unit.g_out = 1.03
        self.upstream_static_gd_unit.T_out = 490
        self.upstream_static_gd_unit.p_stag_out = 1.1e5

        self.atmosphere.update()
        print()
        print('Atmosphere testing')
        print('p_stag_in = %s' % round(self.atmosphere.p_stag_in, -1))
        self.assertNotEqual(self.atmosphere.T_stag_out, None)
        self.assertNotEqual(self.atmosphere.p_stag_out, None)
        self.assertNotEqual(self.atmosphere.p_stag_in, None)
        self.assertNotEqual(self.atmosphere.alpha_out, None)
        self.assertNotEqual(self.atmosphere.g_fuel_out, None)
        self.assertNotEqual(self.atmosphere.g_out, None)
        self.assertNotEqual(self.atmosphere.p_in, None)

    def test_undefined_ports_checking(self):
        solver = NetworkSolver([self.upstream_gd_unit, self.atmosphere, self.downstream_gd_unit])
        solver.create_gas_dynamic_connection(self.upstream_gd_unit, self.atmosphere)
        solver.create_gas_dynamic_connection(self.atmosphere, self.downstream_gd_unit)
        self.assertTrue(self.atmosphere.has_undefined_ports())
        self.atmosphere.set_behaviour()
        self.assertFalse(self.atmosphere.has_undefined_ports())


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.atmosphere = Atmosphere()
        self.inlet = Inlet()
        self.compressor1 = Compressor(6)
        self.compressor2 = Compressor(10, precision=0.001)
        self.sink = Sink()
        self.comb_chamber = CombustionChamber(1400, alpha_out_init=2.7, precision=0.001)
        self.comb_chamber_inter_up = CombustionChamber(1300, alpha_out_init=2.7, precision=0.001)
        self.comb_chamber_inter_down = CombustionChamber(1300, alpha_out_init=2.7, precision=0.001,
                                                         p_stag_out_init=4e5)
        self.source1 = Source(work_fluid=KeroseneCombustionProducts(), g_return=0.03)
        self.source2 = Source(work_fluid=KeroseneCombustionProducts(), g_return=0.03)
        self.turbine_low_pres_power = Turbine(p_stag_out_init=1e5)
        self.turbine_comp_up = Turbine()
        self.turbine_high_pres_power = Turbine(p_stag_out_init=4e5, precision=0.001)
        self.turbine_comp_down = Turbine(p_stag_out_init=1e5, precision=0.001)
        self.outlet = Outlet()
        self.load = Load(2e6)
        self.zero_load1 = Load(0)
        self.zero_load2 = Load(0)

    def get_1B_solver(self) -> NetworkSolver:
        solver = NetworkSolver([self.atmosphere, self.outlet, self.sink, self.source1, self.turbine_low_pres_power,
                                self.inlet, self.comb_chamber, self.compressor1, self.load], cold_work_fluid=Air(),
                               hot_work_fluid=NaturalGasCombustionProducts())
        solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        solver.create_gas_dynamic_connection(self.inlet, self.compressor1)
        solver.create_gas_dynamic_connection(self.compressor1, self.sink)
        solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.source1)
        solver.create_gas_dynamic_connection(self.source1, self.turbine_low_pres_power)
        solver.create_gas_dynamic_connection(self.turbine_low_pres_power, self.outlet)
        solver.create_static_gas_dynamic_connection(self.outlet, self.atmosphere)
        solver.create_mechanical_connection(self.turbine_low_pres_power, self.compressor1, self.load)
        return solver

    def get_2N_solver(self) -> NetworkSolver:
        solver = NetworkSolver([self.atmosphere, self.outlet, self.turbine_comp_up, self.sink, self.source1,
                                self.turbine_low_pres_power, self.inlet, self.comb_chamber, self.compressor2,
                                self.load, self.zero_load1, self.zero_load2], cold_work_fluid=Air(),
                               hot_work_fluid=NaturalGasCombustionProducts())
        solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        solver.create_gas_dynamic_connection(self.inlet, self.compressor2)
        solver.create_gas_dynamic_connection(self.compressor2, self.sink)
        solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.source1)
        solver.create_gas_dynamic_connection(self.source1, self.turbine_comp_up)
        solver.create_gas_dynamic_connection(self.turbine_comp_up, self.turbine_low_pres_power)
        solver.create_gas_dynamic_connection(self.turbine_low_pres_power, self.outlet)
        solver.create_static_gas_dynamic_connection(self.outlet, self.atmosphere)
        solver.create_mechanical_connection(self.turbine_low_pres_power, self.load, self.zero_load1)
        solver.create_mechanical_connection(self.turbine_comp_up, self.compressor2, self.zero_load2)
        return solver

    def get_2NIH_solver(self) -> NetworkSolver:
        solver = NetworkSolver([self.atmosphere, self.outlet, self.turbine_comp_up, self.sink, self.source1,
                                self.turbine_low_pres_power, self.inlet, self.comb_chamber, self.compressor2,
                                self.load, self.zero_load1, self.zero_load2, self.comb_chamber_inter_up, self.source2],
                               precision=0.001, cold_work_fluid=Air(),
                               hot_work_fluid=NaturalGasCombustionProducts())
        solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        solver.create_gas_dynamic_connection(self.inlet, self.compressor2)
        solver.create_gas_dynamic_connection(self.compressor2, self.sink)
        solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.source1)
        solver.create_gas_dynamic_connection(self.source1, self.turbine_comp_up)
        solver.create_gas_dynamic_connection(self.turbine_comp_up, self.comb_chamber_inter_up)
        solver.create_gas_dynamic_connection(self.comb_chamber_inter_up, self.source2)
        solver.create_gas_dynamic_connection(self.source2, self.turbine_low_pres_power)
        solver.create_gas_dynamic_connection(self.turbine_low_pres_power, self.outlet)
        solver.create_static_gas_dynamic_connection(self.outlet, self.atmosphere)
        solver.create_mechanical_connection(self.turbine_low_pres_power, self.load, self.zero_load1)
        solver.create_mechanical_connection(self.turbine_comp_up, self.compressor2, self.zero_load2)
        return solver

    def get_2V_solver(self) -> NetworkSolver:
        solver = NetworkSolver([self.load, self.zero_load1, self.zero_load2, self.atmosphere, self.outlet, self.inlet,
                                self.turbine_comp_down, self.compressor2, self.turbine_high_pres_power,
                                self.comb_chamber, self.sink, self.source1, self.source2], precision=0.0005,
                               cold_work_fluid=Air(),
                               hot_work_fluid=NaturalGasCombustionProducts())
        solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        solver.create_gas_dynamic_connection(self.inlet, self.compressor2)
        solver.create_gas_dynamic_connection(self.compressor2, self.sink)
        solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.source1)
        solver.create_gas_dynamic_connection(self.source1, self.turbine_high_pres_power)
        solver.create_gas_dynamic_connection(self.turbine_high_pres_power, self.source2)
        solver.create_gas_dynamic_connection(self.source2, self.turbine_comp_down)
        solver.create_gas_dynamic_connection(self.turbine_comp_down, self.outlet)
        solver.create_static_gas_dynamic_connection(self.outlet, self.atmosphere)
        solver.create_mechanical_connection(self.turbine_high_pres_power, self.load, self.zero_load1)
        solver.create_mechanical_connection(self.turbine_comp_down, self.compressor2, self.zero_load2)
        return solver

    def get_2VIH_solver(self) -> NetworkSolver:
        solver = NetworkSolver([self.load, self.zero_load1, self.zero_load2, self.atmosphere, self.outlet, self.inlet,
                                self.turbine_comp_down, self.compressor2, self.turbine_high_pres_power,
                                self.comb_chamber, self.sink, self.source1, self.source2,
                                self.comb_chamber_inter_down], precision=0.0005, cold_work_fluid=Air(),
                               hot_work_fluid=NaturalGasCombustionProducts())
        solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        solver.create_gas_dynamic_connection(self.inlet, self.compressor2)
        solver.create_gas_dynamic_connection(self.compressor2, self.sink)
        solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        solver.create_gas_dynamic_connection(self.comb_chamber, self.source1)
        solver.create_gas_dynamic_connection(self.source1, self.turbine_high_pres_power)
        solver.create_gas_dynamic_connection(self.turbine_high_pres_power, self.comb_chamber_inter_down)
        solver.create_gas_dynamic_connection(self.comb_chamber_inter_down, self.source2)
        solver.create_gas_dynamic_connection(self.source2, self.turbine_comp_down)
        solver.create_gas_dynamic_connection(self.turbine_comp_down, self.outlet)
        solver.create_static_gas_dynamic_connection(self.outlet, self.atmosphere)
        solver.create_mechanical_connection(self.turbine_high_pres_power, self.load, self.zero_load1)
        solver.create_mechanical_connection(self.turbine_comp_down, self.compressor2, self.zero_load2)
        return solver

    def test_1B_behaviour_setting(self):
        solver = self.get_1B_solver()
        self.assertTrue(self.atmosphere.has_undefined_ports())
        self.assertTrue(self.inlet.has_undefined_ports())
        self.assertTrue(self.sink.has_undefined_ports())
        self.assertTrue(self.compressor1.has_undefined_ports())
        self.assertTrue(self.comb_chamber.has_undefined_ports())
        self.assertTrue(self.source1.has_undefined_ports())
        self.assertTrue(self.turbine_low_pres_power.has_undefined_ports())
        self.assertTrue(self.outlet.has_undefined_ports())

        solver.set_units_behaviour()

        self.assertFalse(self.atmosphere.has_undefined_ports())
        self.assertFalse(self.inlet.has_undefined_ports())
        self.assertFalse(self.compressor1.has_undefined_ports())
        self.assertFalse(self.sink.has_undefined_ports())
        self.assertFalse(self.comb_chamber.has_undefined_ports())
        self.assertFalse(self.source1.has_undefined_ports())
        self.assertFalse(self.turbine_low_pres_power.has_undefined_ports())
        self.assertFalse(self.outlet.has_undefined_ports())

        self.assertTrue(self.source1.check_upstream_behaviour())
        self.assertTrue(self.comb_chamber.check_upstream_behaviour())
        self.assertFalse(self.comb_chamber.check_downstream_behaviour())
        self.assertTrue(self.turbine_low_pres_power.check_power_turbine_behaviour())
        self.assertFalse(self.turbine_low_pres_power.check_downstream_compressor_turbine_behaviour())
        self.assertFalse(self.turbine_low_pres_power.check_upstream_compressor_turbine_behaviour())

    def test_1B_sorting_units(self):
        solver = self.get_1B_solver()
        sorted_list = solver.get_sorted_unit_list()
        self.assertEqual(sorted_list[0], self.atmosphere)
        self.assertEqual(sorted_list[1], self.inlet)
        self.assertEqual(sorted_list[2], self.compressor1)
        self.assertEqual(sorted_list[3], self.sink)
        self.assertEqual(sorted_list[4], self.comb_chamber)
        self.assertEqual(sorted_list[5], self.source1)
        self.assertEqual(sorted_list[6], self.turbine_low_pres_power)
        self.assertEqual(sorted_list[7], self.outlet)

    def test_1B_solving(self):
        solver = self.get_1B_solver()
        solver.solve()

        print()
        print('1B scheme solving testing')
        print('pi_power_turb = %.4f' % self.turbine_low_pres_power.pi_t)
        print('T_power_turb_out = %.1f' % self.turbine_low_pres_power.T_stag_out)
        print('T_out = %.2f' % self.atmosphere.T_stag_in)
        print('g_comb_in = %.4f' % self.comb_chamber.g_in)
        print('g_comb_out = %.4f' % self.comb_chamber.g_out)
        print('g_turb_in = %.4f' % self.turbine_low_pres_power.g_in)
        print('alpha_turb_in = %.4f' % self.turbine_low_pres_power.alpha_in)
        print('T_comp_out = %.1f' % self.compressor1.T_stag_out)
        print('g_fuel = %.4f' % self.comb_chamber.g_fuel_prime)
        # проверка баланса давлений
        self.assertAlmostEqual(abs(1 - self.atmosphere.p_stag_out * self.inlet.sigma *
                                   self.outlet.sigma * self.comb_chamber.sigma_comb * self.compressor1.pi_c /
                                   (self.atmosphere.p_stag_in * self.turbine_low_pres_power.pi_t)), 0, places=4)

    def test_2N_behaviour_setting(self):
        solver = self.get_2N_solver()

        self.assertTrue(self.atmosphere.has_undefined_ports())
        self.assertTrue(self.inlet.has_undefined_ports())
        self.assertTrue(self.sink.has_undefined_ports())
        self.assertTrue(self.compressor2.has_undefined_ports())
        self.assertTrue(self.comb_chamber.has_undefined_ports())
        self.assertTrue(self.source1.has_undefined_ports())
        self.assertTrue(self.turbine_low_pres_power.has_undefined_ports())
        self.assertTrue(self.turbine_comp_up.has_undefined_ports())
        self.assertTrue(self.outlet.has_undefined_ports())

        solver.set_units_behaviour()

        self.assertFalse(self.atmosphere.has_undefined_ports())
        self.assertFalse(self.inlet.has_undefined_ports())
        self.assertFalse(self.compressor2.has_undefined_ports())
        self.assertFalse(self.sink.has_undefined_ports())
        self.assertFalse(self.comb_chamber.has_undefined_ports())
        self.assertFalse(self.source1.has_undefined_ports())
        self.assertFalse(self.turbine_low_pres_power.has_undefined_ports())
        self.assertFalse(self.turbine_comp_up.has_undefined_ports())
        self.assertFalse(self.outlet.has_undefined_ports())

        self.assertTrue(self.turbine_low_pres_power.check_power_turbine_behaviour())
        self.assertTrue(self.turbine_comp_up.check_upstream_compressor_turbine_behaviour())
        self.assertTrue(self.comb_chamber.check_upstream_behaviour())
        self.assertTrue(self.source1.check_upstream_behaviour())

    def test_2N_sorting_units(self):
        solver = self.get_2N_solver()

        sorted_list = solver.get_sorted_unit_list()

        self.assertEqual(sorted_list[0], self.atmosphere)
        self.assertEqual(sorted_list[1], self.inlet)
        self.assertEqual(sorted_list[2], self.compressor2)
        self.assertEqual(sorted_list[3], self.sink)
        self.assertEqual(sorted_list[4], self.comb_chamber)
        self.assertEqual(sorted_list[5], self.source1)
        self.assertEqual(sorted_list[6], self.turbine_comp_up)
        self.assertEqual(sorted_list[7], self.turbine_low_pres_power)
        self.assertEqual(sorted_list[8], self.outlet)

    def test_2N_solving(self):
        solver = self.get_2N_solver()
        solver.solve()

        print()
        print('2N scheme solving testing')
        print('pi_power_turb = %.4f' % self.turbine_low_pres_power.pi_t)
        print('pi_comp_turb = %.4f' % self.turbine_comp_up.pi_t)
        print('T_power_turb_out = %.1f' % self.turbine_low_pres_power.T_stag_out)
        print('T_comp_turb_out = %.1f' % self.turbine_comp_up.T_stag_out)
        print('T_out = %.2f' % self.atmosphere.T_stag_in)
        print('g_comb_in = %.4f' % self.comb_chamber.g_in)
        print('g_comb_out = %.4f' % self.comb_chamber.g_out)
        print('g_turb_in = %.4f' % self.turbine_comp_up.g_in)
        print('alpha_turb_in = %.4f' % self.turbine_comp_up.alpha_in)
        print('T_comp_out = %.1f' % self.compressor2.T_stag_out)
        print('g_fuel = %.4f' % self.comb_chamber.g_fuel_prime)
        # проверка баланса давлений
        self.assertAlmostEqual(abs(1 - self.atmosphere.p_stag_out * self.inlet.sigma *
                                   self.outlet.sigma * self.comb_chamber.sigma_comb * self.compressor2.pi_c /
                                   (self.atmosphere.p_stag_in * self.turbine_low_pres_power.pi_t *
                                    self.turbine_comp_up.pi_t)), 0, places=4)

    def test_2V_behaviour_setting(self):
        solver = self.get_2V_solver()

        self.assertTrue(self.atmosphere.has_undefined_ports())
        self.assertTrue(self.inlet.has_undefined_ports())
        self.assertTrue(self.compressor2.has_undefined_ports())
        self.assertTrue(self.sink.has_undefined_ports())
        self.assertTrue(self.comb_chamber.has_undefined_ports())
        self.assertTrue(self.source1.has_undefined_ports())
        self.assertTrue(self.turbine_high_pres_power.has_undefined_ports())
        self.assertTrue(self.source2.has_undefined_ports())
        self.assertTrue(self.turbine_comp_down.has_undefined_ports())
        self.assertTrue(self.outlet.has_undefined_ports())

        solver.set_units_behaviour()

        self.assertFalse(self.atmosphere.has_undefined_ports())
        self.assertFalse(self.inlet.has_undefined_ports())
        self.assertFalse(self.compressor2.has_undefined_ports())
        self.assertFalse(self.sink.has_undefined_ports())
        self.assertFalse(self.comb_chamber.has_undefined_ports())
        self.assertFalse(self.source1.has_undefined_ports())
        self.assertFalse(self.turbine_high_pres_power.has_undefined_ports())
        self.assertFalse(self.source2.has_undefined_ports())
        self.assertFalse(self.turbine_comp_down.has_undefined_ports())
        self.assertFalse(self.outlet.has_undefined_ports())

        self.assertTrue(self.comb_chamber.check_upstream_behaviour())
        self.assertTrue(self.source1.check_upstream_behaviour())
        self.assertTrue(self.source2.check_downstream_behaviour())
        self.assertTrue(self.turbine_high_pres_power.check_power_turbine_behaviour())
        self.assertTrue(self.turbine_comp_down.check_downstream_compressor_turbine_behaviour())

    def test_2V_sorting(self):
        solver = self.get_2V_solver()
        sorted_list = solver.get_sorted_unit_list()

        self.assertEqual(sorted_list[0], self.atmosphere)
        self.assertEqual(sorted_list[1], self.inlet)
        self.assertEqual(sorted_list[2], self.compressor2)
        self.assertEqual(sorted_list[3], self.sink)
        self.assertEqual(sorted_list[4], self.comb_chamber)
        self.assertEqual(sorted_list[5], self.source1)
        self.assertEqual(sorted_list[6], self.turbine_high_pres_power)
        self.assertEqual(sorted_list[7], self.source2)
        self.assertEqual(sorted_list[8], self.turbine_comp_down)
        self.assertEqual(sorted_list[9], self.outlet)

    def test_2V_solving(self):
        solver = self.get_2V_solver()
        solver.solve()

        print()
        print('2V scheme solving testing')
        print('pi_power_turb = %.4f' % self.turbine_high_pres_power.pi_t)
        print('pi_comp_turb = %.4f' % self.turbine_comp_down.pi_t)
        print('T_power_turb_out = %.1f' % self.turbine_high_pres_power.T_stag_out)
        print('T_comp_turb_out = %.1f' % self.turbine_comp_down.T_stag_out)
        print('T_out = %.2f' % self.atmosphere.T_stag_in)
        print('g_comb_in = %.4f' % self.comb_chamber.g_in)
        print('g_comb_out = %.4f' % self.comb_chamber.g_out)
        print('g_power_turb_in = %.4f' % self.turbine_high_pres_power.g_in)
        print('g_comp_turb_in = %.4f' % self.turbine_comp_down.g_in)
        print('alpha_turb_in = %.4f' % self.turbine_high_pres_power.alpha_in)
        print('T_comp_out = %.1f' % self.compressor2.T_stag_out)
        print('g_fuel = %.4f' % self.comb_chamber.g_fuel_prime)

        # проверка баланса давлений
        self.assertAlmostEqual(abs(1 - self.atmosphere.p_stag_out * self.inlet.sigma *
                                   self.outlet.sigma * self.comb_chamber.sigma_comb * self.compressor2.pi_c /
                                   (self.atmosphere.p_stag_in * self.turbine_high_pres_power.pi_t *
                                    self.turbine_comp_down.pi_t)), 0, places=3)

    def test_2NIH_behaviour_setting(self):
        solver = self.get_2NIH_solver()

        self.assertTrue(self.atmosphere.has_undefined_ports())
        self.assertTrue(self.inlet.has_undefined_ports())
        self.assertTrue(self.sink.has_undefined_ports())
        self.assertTrue(self.compressor2.has_undefined_ports())
        self.assertTrue(self.comb_chamber.has_undefined_ports())
        self.assertTrue(self.source1.has_undefined_ports())
        self.assertTrue(self.turbine_low_pres_power.has_undefined_ports())
        self.assertTrue(self.comb_chamber_inter_up.has_undefined_ports())
        self.assertTrue(self.source2.has_undefined_ports())
        self.assertTrue(self.turbine_comp_up.has_undefined_ports())
        self.assertTrue(self.outlet.has_undefined_ports())

        solver.set_units_behaviour()

        self.assertFalse(self.atmosphere.has_undefined_ports())
        self.assertFalse(self.inlet.has_undefined_ports())
        self.assertFalse(self.compressor2.has_undefined_ports())
        self.assertFalse(self.sink.has_undefined_ports())
        self.assertFalse(self.comb_chamber.has_undefined_ports())
        self.assertFalse(self.source1.has_undefined_ports())
        self.assertFalse(self.turbine_low_pres_power.has_undefined_ports())
        self.assertFalse(self.comb_chamber_inter_up.has_undefined_ports())
        self.assertFalse(self.source2.has_undefined_ports())
        self.assertFalse(self.turbine_comp_up.has_undefined_ports())
        self.assertFalse(self.outlet.has_undefined_ports())

        self.assertTrue(self.turbine_low_pres_power.check_power_turbine_behaviour())
        self.assertTrue(self.turbine_comp_up.check_upstream_compressor_turbine_behaviour())
        self.assertTrue(self.comb_chamber.check_upstream_behaviour())
        self.assertTrue(self.source1.check_upstream_behaviour())
        self.assertTrue(self.source2.check_upstream_behaviour())
        self.assertTrue(self.comb_chamber_inter_up.check_upstream_behaviour())

    def test_2NIH_sorting_units(self):
        solver = self.get_2NIH_solver()

        sorted_list = solver.get_sorted_unit_list()

        self.assertEqual(sorted_list[0], self.atmosphere)
        self.assertEqual(sorted_list[1], self.inlet)
        self.assertEqual(sorted_list[2], self.compressor2)
        self.assertEqual(sorted_list[3], self.sink)
        self.assertEqual(sorted_list[4], self.comb_chamber)
        self.assertEqual(sorted_list[5], self.source1)
        self.assertEqual(sorted_list[6], self.turbine_comp_up)
        self.assertEqual(sorted_list[7], self.comb_chamber_inter_up)
        self.assertEqual(sorted_list[8], self.source2)
        self.assertEqual(sorted_list[9], self.turbine_low_pres_power)
        self.assertEqual(sorted_list[10], self.outlet)

    def test_2NIH_solving(self):
        solver = self.get_2NIH_solver()
        solver.solve()

        print()
        print('2NIV scheme solving testing')
        print('pi_power_turb = %.4f' % self.turbine_low_pres_power.pi_t)
        print('pi_comp_turb = %.4f' % self.turbine_comp_up.pi_t)
        print('T_power_turb_out = %.1f' % self.turbine_low_pres_power.T_stag_out)
        print('T_comp_turb_out = %.1f' % self.turbine_comp_up.T_stag_out)
        print('T_out = %.2f' % self.atmosphere.T_stag_in)
        print('g_comb_in = %.4f' % self.comb_chamber.g_in)
        print('g_comb_out = %.4f' % self.comb_chamber.g_out)
        print('g_fuel_comb_prime = %.4f' % self.comb_chamber.g_fuel_prime)
        print('g_comp_turb_in = %.4f' % self.turbine_comp_up.g_in)
        print('alpha_comp_turb_in = %.4f' % self.turbine_comp_up.alpha_in)
        print('g_fuel_ih_in = %.4f' % self.comb_chamber_inter_up.g_fuel_in)
        print('g_fuel_ih_out = %.4f' % self.comb_chamber_inter_up.g_fuel_out)
        print('g_fuel_ih_prime = %.4f' % self.comb_chamber_inter_up.g_fuel_prime)
        print('g_power_turb_in = %.4f' % self.turbine_low_pres_power.g_in)
        print('alpha_power_turb_in = %.4f' % self.turbine_low_pres_power.alpha_in)
        print('T_comp_out = %.1f' % self.compressor2.T_stag_out)

        # проверка баланса давлений
        self.assertAlmostEqual(abs(1 - self.atmosphere.p_stag_out * self.inlet.sigma *
                                   self.outlet.sigma * self.comb_chamber.sigma_comb *
                                   self.comb_chamber_inter_up.sigma_comb * self.compressor2.pi_c /
                                   (self.atmosphere.p_stag_in * self.turbine_low_pres_power.pi_t *
                                    self.turbine_comp_up.pi_t)), 0, places=4)

    def test_2VIH_behaviour_setting(self):
        solver = self.get_2VIH_solver()

        self.assertTrue(self.atmosphere.has_undefined_ports())
        self.assertTrue(self.inlet.has_undefined_ports())
        self.assertTrue(self.compressor2.has_undefined_ports())
        self.assertTrue(self.sink.has_undefined_ports())
        self.assertTrue(self.comb_chamber.has_undefined_ports())
        self.assertTrue(self.source1.has_undefined_ports())
        self.assertTrue(self.turbine_high_pres_power.has_undefined_ports())
        self.assertTrue(self.comb_chamber_inter_down.has_undefined_ports())
        self.assertTrue(self.source2.has_undefined_ports())
        self.assertTrue(self.turbine_comp_down.has_undefined_ports())
        self.assertTrue(self.outlet.has_undefined_ports())

        solver.set_units_behaviour()

        self.assertFalse(self.atmosphere.has_undefined_ports())
        self.assertFalse(self.inlet.has_undefined_ports())
        self.assertFalse(self.compressor2.has_undefined_ports())
        self.assertFalse(self.sink.has_undefined_ports())
        self.assertFalse(self.comb_chamber.has_undefined_ports())
        self.assertFalse(self.source1.has_undefined_ports())
        self.assertFalse(self.turbine_high_pres_power.has_undefined_ports())
        self.assertFalse(self.comb_chamber_inter_down.has_undefined_ports())
        self.assertFalse(self.source2.has_undefined_ports())
        self.assertFalse(self.turbine_comp_down.has_undefined_ports())
        self.assertFalse(self.outlet.has_undefined_ports())

        self.assertTrue(self.comb_chamber.check_upstream_behaviour())
        self.assertTrue(self.source1.check_upstream_behaviour())
        self.assertTrue(self.source2.check_downstream_behaviour())
        self.assertTrue(self.turbine_high_pres_power.check_power_turbine_behaviour())
        self.assertTrue(self.comb_chamber_inter_down.check_downstream_behaviour())
        self.assertTrue(self.turbine_comp_down.check_downstream_compressor_turbine_behaviour())

    def test_2VIH_sorting(self):
        solver = self.get_2VIH_solver()
        sorted_list = solver.get_sorted_unit_list()

        self.assertEqual(sorted_list[0], self.atmosphere)
        self.assertEqual(sorted_list[1], self.inlet)
        self.assertEqual(sorted_list[2], self.compressor2)
        self.assertEqual(sorted_list[3], self.sink)
        self.assertEqual(sorted_list[4], self.comb_chamber)
        self.assertEqual(sorted_list[5], self.source1)
        self.assertEqual(sorted_list[6], self.turbine_high_pres_power)
        self.assertEqual(sorted_list[7], self.comb_chamber_inter_down)
        self.assertEqual(sorted_list[8], self.source2)
        self.assertEqual(sorted_list[9], self.turbine_comp_down)
        self.assertEqual(sorted_list[10], self.outlet)

    def test_2VIH_solving(self):
        solver = self.get_2VIH_solver()
        solver.solve()

        print()
        print('2VIH scheme solving testing')
        print('Iter number = %s' % solver.iter_number)
        print('pi_power_turb = %.4f' % self.turbine_high_pres_power.pi_t)
        print('pi_comp_turb = %.4f' % self.turbine_comp_down.pi_t)
        print('T_power_turb_out = %.1f' % self.turbine_high_pres_power.T_stag_out)
        print('T_comp_turb_out = %.1f' % self.turbine_comp_down.T_stag_out)
        print('T_out = %.2f' % self.atmosphere.T_stag_in)
        print('g_comb_in = %.4f' % self.comb_chamber.g_in)
        print('g_comb_out = %.4f' % self.comb_chamber.g_out)
        print('g_fuel_comb_prime = %.4f' % self.comb_chamber.g_fuel_prime)
        print('g_fuel_comb_out = %.4f' % self.comb_chamber.g_fuel_out)
        print('g_ih_in = %.4f' % self.comb_chamber_inter_down.g_in)
        print('g_ih_out = %.4f' % self.comb_chamber_inter_down.g_out)
        print('g_fuel_ih_prime = %.4f' % self.comb_chamber_inter_down.g_fuel_prime)
        print('g_fuel_ih_out = %.4f' % self.comb_chamber_inter_down.g_fuel_out)
        print('g_power_turb_in = %.4f' % self.turbine_high_pres_power.g_in)
        print('g_comp_turb_in = %.4f' % self.turbine_comp_down.g_in)
        print('alpha_power_turb_in = %.4f' % self.turbine_high_pres_power.alpha_in)
        print('alpha_comp_turb_in = %.4f' % self.turbine_comp_down.alpha_in)
        print('T_comp_out = %.1f' % self.compressor2.T_stag_out)

        # проверка баланса давлений
        self.assertAlmostEqual(abs(1 - self.atmosphere.p_stag_out * self.inlet.sigma *
                                   self.outlet.sigma * self.comb_chamber.sigma_comb * self.compressor2.pi_c *
                                   self.comb_chamber_inter_down.sigma_comb /
                                   (self.atmosphere.p_stag_in * self.turbine_high_pres_power.pi_t *
                                    self.turbine_comp_down.pi_t)), 0, places=3)

    def test_2VIH_work_fluids(self):
        solver = self.get_2VIH_solver()
        solver.solve()

        self.assertEqual(type(self.atmosphere.work_fluid_in), NaturalGasCombustionProducts)
        self.assertEqual(type(self.comb_chamber.work_fluid_in), Air)
        self.assertEqual(type(self.comb_chamber.work_fluid_out), NaturalGasCombustionProducts)
        self.assertEqual(type(self.comb_chamber_inter_down.work_fluid_in), NaturalGasCombustionProducts)
        self.assertEqual(type(self.comb_chamber_inter_down.work_fluid_out), NaturalGasCombustionProducts)
        self.assertEqual(type(self.turbine_comp_down.work_fluid), NaturalGasCombustionProducts)
        self.assertEqual(type(self.outlet.work_fluid), NaturalGasCombustionProducts)
        self.assertEqual(type(self.turbine_high_pres_power.work_fluid), NaturalGasCombustionProducts)


if __name__ == '__main__':
    unittest.main(verbosity=1)