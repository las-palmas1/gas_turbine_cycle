import unittest
from gas_turbine_cycle.core.solver import NetworkSolver
from gas_turbine_cycle.core.turbine_lib import Compressor, Turbine, Source, Sink, CombustionChamber, Inlet, Outlet, \
    Atmosphere, Load
from gas_turbine_cycle.gases import KeroseneCombustionProducts, NaturalGasCombustionProducts, Air
from jinja2 import Template, Environment, select_autoescape, FileSystemLoader
import os


class TemplateTester(unittest.TestCase):
    def setUp(self):
        self.atmosphere = Atmosphere()
        self.inlet = Inlet()
        self.compressor = Compressor(10, precision=0.001)
        self.sink = Sink()
        self.comb_chamber = CombustionChamber(1400, alpha_out_init=2.7, precision=0.001)
        self.comb_chamber_inter_up = CombustionChamber(1300, alpha_out_init=2.7, precision=0.001)
        self.comb_chamber_inter_down = CombustionChamber(1300, alpha_out_init=2.7, precision=0.001,
                                                         p_stag_out_init=4e5)
        self.source1 = Source()
        self.source2 = Source()
        self.turbine_low_pres_power = Turbine(p_stag_out_init=1e5)
        self.turbine_comp_up = Turbine()
        self.outlet = Outlet()
        self.load = Load(2e6)
        self.zero_load1 = Load(0)
        self.zero_load2 = Load(0)
        self.solver = NetworkSolver([self.atmosphere, self.outlet, self.turbine_comp_up, self.sink, self.source1,
                                     self.turbine_low_pres_power, self.inlet, self.comb_chamber, self.compressor,
                                     self.load, self.zero_load1, self.zero_load2], cold_work_fluid=Air(),
                                     hot_work_fluid=NaturalGasCombustionProducts())
        self.solver.create_gas_dynamic_connection(self.atmosphere, self.inlet)
        self.solver.create_gas_dynamic_connection(self.inlet, self.compressor)
        self.solver.create_gas_dynamic_connection(self.compressor, self.sink)
        self.solver.create_gas_dynamic_connection(self.sink, self.comb_chamber)
        self.solver.create_gas_dynamic_connection(self.comb_chamber, self.source1)
        self.solver.create_gas_dynamic_connection(self.source1, self.turbine_comp_up)
        self.solver.create_gas_dynamic_connection(self.turbine_comp_up, self.turbine_low_pres_power)
        self.solver.create_gas_dynamic_connection(self.turbine_low_pres_power, self.outlet)
        self.solver.create_gas_dynamic_connection(self.outlet, self.atmosphere)
        self.solver.create_mechanical_connection(self.turbine_low_pres_power, self.load, self.zero_load1)
        self.solver.create_mechanical_connection(self.turbine_comp_up, self.compressor, self.zero_load2)
        self.solver.solve()

    def test_2N_template(self):
        loader = FileSystemLoader([os.path.dirname(os.path.dirname(__file__)), os.path.dirname(__file__)])
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
            source1=self.source1,
            turb_c=self.turbine_comp_up,
            source2=self.source2,
            turb_p=self.turbine_low_pres_power,
            outlet=self.outlet,
            load=self.load
        )
        with open('report_test.tex', 'w', encoding='utf-8') as file:
            file.write(content)