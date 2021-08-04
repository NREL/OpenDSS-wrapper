import os
import datetime as dt
import pandas as pd

from opendss_wrapper import OpenDSS

pd.set_option('max_columns', None)  # Prints all columns
pd.set_option('expand_frame_repr', False)  # Keeps results on 1 line
pd.set_option('precision', 3)

"""
Script to test the IEEE13 test feeder
"""

# Path variables
this_dir = os.path.abspath(os.path.dirname(__file__))
master_dss_file = os.path.join(this_dir, 'IEEE13Nodeckt.dss')

# Timing variables
time_res = dt.timedelta(minutes=1)
start_time = dt.datetime(2019, 1, 1)

# Create OpenDSS Object
d = OpenDSS(master_dss_file, time_res, start_time)

# Run 1 timestep
print()
print('Running 1 time step...')
d.run_dss()
print()

# Check circuit functions
print('Circuit info:')
info = d.get_circuit_info()
for key, val in info.items():
    print(f'{key:20} -> {val:11.8f}')
print()

# All Element Names
print('DSS Elements: ', d.dss.Circuit.AllElementNames())
print()

# Check bus voltages
buses = d.get_all_buses()
bus0 = buses[0]
print('All Bus names:', buses)
print('First Bus voltage:', d.get_bus_voltage(bus0))
print('First Bus voltage, phase 1:', d.get_bus_voltage(bus0, phase=1))
print('First Bus voltage, complex:', d.get_bus_voltage(bus0, polar=False, pu=False))
print('First Bus voltage, MagAng:', d.get_bus_voltage(bus0, mag_only=False))
print()

# All Loads, as dataframe
df_loads = d.get_all_elements()
print('First 5 Loads (DataFrame)')
print(df_loads.head())
print()

# Check load functions
load_3ph = df_loads.index[0]
load_1ph = df_loads.index[1]
print('3 Phase Load voltage:', d.get_voltage(load_3ph))
print('3 Phase Load powers ((P1, P2, P3), (Q1, Q2, Q3)):', d.get_power(load_3ph))
print('1 Phase Load voltage:', d.get_voltage(load_1ph))
print('1 Phase Load powers (P1, Q1):', d.get_power(load_1ph))
print()

# Set load power and then check
d.set_power(load_1ph, p=100, q=50)
d.run_dss()
print('1 Phase Load powers after update:', d.get_power(load_1ph))
print()

# All Transformers, as dataframe
df_xfmr = d.get_all_elements('Xfmr')
print('First 5 Transformers (DataFrame)')
print(df_xfmr.head())
print()

# Check Xfmr functions
xfmr0 = df_xfmr.index[0]
print('First Xfmr powers, first bus:', d.get_power(xfmr0, element='Xfmr'))
print('First Xfmr powers, second bus:', d.get_power(xfmr0, element='Xfmr', line_bus=2))
print('First Xfmr voltages:', d.get_voltage(xfmr0, element='Xfmr'))
