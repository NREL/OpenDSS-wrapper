import os
import datetime as dt
import pandas as pd

from opendss_wrapper import OpenDSS

pd.set_option('max_columns', None)  # Prints all columns
pd.set_option('expand_frame_repr', False)  # Keeps results on 1 line
pd.set_option('precision', 3)

"""
Script to test a battery on the IEEE13 test feeder
"""

# Path variables
this_dir = os.path.abspath(os.path.dirname(__file__))
master_dss_file = os.path.join(this_dir, 'IEEE13Nodeckt.dss')

# Timing variables
time_res = dt.timedelta(minutes=1)
start_time = dt.datetime(2019, 1, 1)

# Create OpenDSS Object
d = OpenDSS(master_dss_file, time_res, start_time)

# Create Battery
d.run_command('new Storage.battery1 phases=3 Bus1=671.1.2.3 kV=4.16 kVA=5 kWRated=5 kWhRated=10 %reserve=10 %stored=50'
              ' %EffCharge=95 %EffDischarge=95 %IdlingkW=0')

# Run simulation for 1 day
time_range = pd.date_range(start_time, start_time + dt.timedelta(days=1), freq=time_res)
results = []
for t in time_range:
    # set battery power on daily schedule
    hour = t.hour
    if 9 <= hour < 15:
        p_set = 1
    elif 17 <= hour < 21:
        p_set = -3
    else:
        p_set = 0
    d.set_power('battery1', p_set, element='Storage')

    # Run model
    d.run_dss()

    # get battery power and SOC
    p_out, _ = d.get_power('battery1', element='Storage', total=True)
    soc = d.get_property('battery1', '%stored', 'Storage') / 100  # percent to fraction
    results.append({'Time': t, 'Power (kW)': p_out, 'SOC (-)': soc})

df = pd.DataFrame(results)
df.to_csv(os.path.join(this_dir, 'battery_results.csv'))
