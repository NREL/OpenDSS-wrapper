import os
import datetime as dt
import pandas as pd
from pyparsing import ZeroOrMore

from opendss_wrapper import OpenDSS

pd.set_option('display.precision', 3)      # precision in print statements
pd.set_option('expand_frame_repr', False)  # Keeps results on 1 line
pd.set_option('display.max_rows', 30)      # Shows up to 30 rows of data
# pd.set_option('max_columns', None)       # Prints all columns

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
feeder = OpenDSS(master_dss_file, time_res, start_time)

# Run 1 timestep
print()
print('Running 1 time step...')
feeder.run_dss()
print()

# Get circuit info
print('Circuit info:')
info = feeder.get_circuit_info()
for key, val in info.items():
    print(f'{key:20} -> {val:11.8f}')
print()

# Get all element names
print('DSS Elements: ', feeder.dss.Circuit.AllElementNames())
print()

# Get bus voltages
buses = feeder.get_all_buses()
last_bus = buses[-1]
print('All Bus names:', buses)
print('Last Bus voltage:', feeder.get_bus_voltage(last_bus))
print('Last Bus voltage, phase 1:', feeder.get_bus_voltage(last_bus, phase=1))
print('Last Bus voltage, complex:', feeder.get_bus_voltage(last_bus, polar=False, pu=False))
print('Last Bus voltage, magnitudes and angles:', feeder.get_bus_voltage(last_bus, mag_only=False, pu=False))
print()

# Get all loads, as dataframe
df_loads = feeder.get_all_elements()
print('First 5 Loads (DataFrame)')
print(df_loads.head())
print()

# Get load info (verified that P=VI* for 3-phase loads)
load_3ph = df_loads.index[0]
load_1ph = df_loads.index[1]
print('3 Phase Load base voltage (kV):', feeder.get_property(load_3ph, 'kV'))
print('3 Phase Load voltage (magnitudes):', feeder.get_voltage(load_3ph))
print('3 Phase Load voltage (phase 1 only):', feeder.get_voltage(load_3ph, phase=1))
print('3 Phase Load voltage (complex):', feeder.get_voltage(load_3ph, polar=False))
print('3 Phase Load powers ((P1, P2, P3), (Q1, Q2, Q3)):', feeder.get_power(load_3ph))
print('3 Phase Load powers (total P, total Q):', feeder.get_power(load_3ph, total=True))
print('3 Phase Load current (total):', feeder.get_current(load_3ph, total=True))
print('3 Phase Load current (complex):', feeder.get_current(load_3ph, polar=False))
print()
print('1 Phase Load voltage:', feeder.get_voltage(load_1ph))
print('1 Phase Load powers (P1, Q1):', feeder.get_power(load_1ph))
print('1 Phase Load current:', feeder.get_current(load_1ph))
print()

# Set load power and verify
feeder.set_power(load_1ph, p=100, q=50)
feeder.run_dss()
print('1 Phase Load powers after update:', feeder.get_power(load_1ph))
print()

# Get all transformers, as dataframe
df_xfmr = feeder.get_all_elements('Xfmr')
print('First 5 Transformers (DataFrame)')
print(df_xfmr.head())
print()

# Get Xfmr info (works for lines and capacitors too)
xfmr0 = df_xfmr.index[0]
print('First Xfmr powers, first bus:', feeder.get_power(xfmr0, element='Xfmr'))
print('First Xfmr powers, second bus:', feeder.get_power(xfmr0, element='Xfmr', line_bus=2))
print('First Xfmr voltages (high bus, in V):', feeder.get_voltage(xfmr0, element='Xfmr', pu=False))
print('First Xfmr voltages (low bus, in V):', feeder.get_voltage(xfmr0, element='Xfmr', pu=False, line_bus=2))
print('First Xfmr is open:', feeder.get_is_open(xfmr0, element='Xfmr'))
feeder.set_is_open(xfmr0, True, element='Xfmr')
print('First Xfmr is open:', feeder.get_is_open(xfmr0, element='Xfmr'))
print()

# Get capacitor info
cap0 = feeder.get_all_elements('Capacitor').index[0]
states = feeder.get_property(cap0, 'states', element='Capacitor')
print(f'First Capacitor State:', states)
print()

# Get regcontrol info
reg0 = feeder.get_all_elements('RegControl').index[0]
print(f'First Voltage Regulator Tap:', feeder.get_tap(reg0))
feeder.set_tap(reg0, 10)
print(f'First Voltage Regulator Tap:', feeder.get_tap(reg0))
print()

# Get bus voltage after Xfmr is opened
print('Last Bus voltage (before running):', feeder.get_bus_voltage(last_bus))
print('Running 1 time step...')
feeder.run_dss()
print('Last Bus voltage (after running):', feeder.get_bus_voltage(last_bus))
print('Last Bus voltage:', feeder.get_bus_voltage(last_bus, polar=False))
print()


