import unittest
from gas_turbine_cycle.core.solver import NetworkSolver
from gas_turbine_cycle.core.turbine_lib import Compressor, Turbine, Source, Sink, CombustionChamber, Inlet, Outlet, \
    Atmosphere, Load
from gas_turbine_cycle.gases import KeroseneCombustionProducts, NaturalGasCombustionProducts, Air
from jinja2 import Template, Environment, select_autoescape, FileSystemLoader
import os
import gas_turbine_cycle.templates
import gas_turbine_cycle.templates.test


class TemplateTester(unittest.TestCase):
    def setUp(self):
        self.atmosphere = Atmosphere()
        self.inlet = Inlet()
        self.compressor = Compressor(17, precision=0.001)
        self.sink = Sink(g_cooling=0.05, g_outflow=0.01)
        self.comb_chamber = CombustionChamber(1450, alpha_out_init=2.7, precision=0.001)
        self.comb_chamber_inter_up = CombustionChamber(1300, alpha_out_init=2.7, precision=0.001)
        self.comb_chamber_inter_down = CombustionChamber(1300, alpha_out_init=2.7, precision=0.001,
                                                         p_stag_out_init=4e5)
        self.source = Source(g_return=0.05)
        self.turbine_low_pres_power = Turbine(p_stag_out_init=1e5)
        self.turbine_comp_up = Turbine()
        self.outlet = Outlet()
        self.N_gen = 10e6
        self.eta_gen = 0.97
        self.load = Load(self.N_gen / self.eta_gen)
        self.zero_load1 = Load(0)
        self.zero_load2 = Load(0)
        self.solver = NetworkSolver([self.atmosphere, self.outlet, self.turbine_comp_up, self.sink,
                                     self.turbine_low_pres_power, self.source, self.inlet, self.comb_chamber,
                                     self.compressor,
                                     self.load, self.zero_load1, self.zero_load2], cold_work_fluid=Air(),
                                    hot_work_fluid=NaturalGasCombustionProducts())
        self.solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        self.solver.create_gas_dynamic_connection(self.inlet, self.compressor)
        self.solver.create_gas_dynamic_connection(self.compressor, self.sink)
        self.solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        self.solver.create_gas_dynamic_connection(self.comb_chamber, self.turbine_comp_up)
        self.solver.create_gas_dynamic_connection(self.turbine_comp_up, self.source)
        self.solver.create_gas_dynamic_connection(self.source, self.turbine_low_pres_power)
        self.solver.create_gas_dynamic_connection(self.turbine_low_pres_power, self.outlet)
        self.solver.create_static_gas_dynamic_connection(self.outlet, self.atmosphere)
        self.solver.create_mechanical_connection(self.turbine_low_pres_power, self.load, self.zero_load1)
        self.solver.create_mechanical_connection(self.turbine_comp_up, self.compressor, self.zero_load2)
        self.solver.solve()

        self.N_e_specific = self.load.consumable_labour
        self.G_air = self.load.power / self.N_e_specific
        self.G_fuel = self.comb_chamber.g_fuel_prime * self.comb_chamber.g_in * self.G_air
        self.c_p_nat_gas_av = 2.3e3
        self.k_nat_gas_av = 1.31
        self.press_in_gas_comp = 1.3e6
        self.T_in_gas_comp = 288
        self.eta_ad_gas_comp = 0.82
        self.eta_el_eng = 0.95
        self.mass_rate_gas_comp = self.G_fuel
        self.press_out_gas_comp = self.compressor.p_stag_out + 0.5e6
        self.pi_gas_comp = self.press_out_gas_comp / self.press_in_gas_comp
        self.rho_gas_comp = 6.9867 + (10.587 - 6.9867) / (1.5e6 - 1e6) * (self.press_in_gas_comp - 1e6)
        self.vol_rate_gas_comp = self.mass_rate_gas_comp / self.rho_gas_comp * 60
        self.T_out_gas_comp = self.T_in_gas_comp * (
                1 + (self.pi_gas_comp ** ((self.k_nat_gas_av - 1) / self.k_nat_gas_av) - 1) / self.eta_ad_gas_comp)
        self.L_e_gas_comp = self.c_p_nat_gas_av * (self.T_out_gas_comp - self.T_in_gas_comp)
        self.N_gas_comp = self.L_e_gas_comp / (self.mass_rate_gas_comp * self.eta_el_eng)

    def test_2N_template(self):
        loader = FileSystemLoader(
            [gas_turbine_cycle.templates.__path__[0], gas_turbine_cycle.templates.test.__path__[0]])
        env = Environment(
            loader=loader,
            autoescape=select_autoescape(['tex']),
            block_start_string='</',
            block_end_string='/>',
            variable_start_string='<<',
            variable_end_string='>>'
        )

        report_template = env.get_template('report_test_template.tex')
        content = report_template.render(
            atm=self.atmosphere,
            inlet=self.inlet,
            comp=self.compressor,
            sink=self.sink,
            comb_chamber=self.comb_chamber,
            turb_c=self.turbine_comp_up,
            source=self.source,
            turb_p=self.turbine_low_pres_power,
            outlet=self.outlet,
            load=self.load,
            N_gen=self.N_gen,
            eta_gen=self.eta_gen,
            name_gen='Т-16-2Р УХЛ3.1',
            N_gas_comp=self.N_gas_comp,
            vol_rate_gas_comp=9,
            mass_rate_gas_comp=self.mass_rate_gas_comp,
            press_in_gas_comp=self.press_in_gas_comp,
            press_out_gas_comp=self.press_out_gas_comp,
            T_in_gas_comp=self.T_in_gas_comp,
            T_out_gas_comp=self.T_out_gas_comp,
            rho_gas_comp=self.rho_gas_comp,
            c_p_nat_gas_av=self.c_p_nat_gas_av,
            k_nat_gas_av=self.k_nat_gas_av,
            eta_ad_gas_comp=self.eta_ad_gas_comp,
            eta_el_eng=self.eta_el_eng,
            name_gas_comp='ТАКАТ-9/13-33,5'

        )
        with open('report_test.tex', 'w', encoding='utf-8') as file:
            file.write(content)
