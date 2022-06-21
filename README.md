# OpenDSS-wrapper
Distribution system simulation python wrapper to connect OpenDSSDirect.py with a co-simulation framework

The wrapper contains user-friendly functions for various OpenDSS commands:
* Getting and setting power
* Getting voltage or current for an element or a bus
* Solving in QSTS modes (with or without controls)
* Redirecting (loading) dss files
* Collecting circuit results
* Getting and setting element properties
* Running any other OpenDSS command

## Installation

### In Co-simulation
To embed this in a co-simulation, create an `environment.yml` file in the co-simulation
project and include the following lines:

```
dependencies:
  - pip:
    - git+https://github.com/NREL/OpenDSS-wrapper
```

### Stand-alone Installation

For a stand-alone installation, run:

```
pip install git+https://github.com/NREL/OpenDSS-wrapper
```

Or, download the repository and run the `setup.py` file from the command line:

```
python setup.py install
```

## Usage

The OpenDSS wrapper makes it easy to call OpenDSS commands without knowing any details about OpenDSS syntax.
The following code shows a simple example initialization:

```
import datetime as dt
from opendss_wrapper import OpenDSS
feeder = OpenDSS('master_file.dss',        # path to dss file for redirect
                 dt.timedelta(minutes=1),  # time resolution for QSTS simulation       
                 dt.datetime(2019, 1, 1),  # start time for QSTS simulation
                 )
```

The following lines can be used for common OpenDSS commands:

```
feeder.run_dss()                          # Solve and progress 1 time step
feeder.get_bus_voltage(bus_name)          # Get the voltage at a given bus
feeder.get_voltage(load_name)             # Get the voltage at the bus of a given circuit element
feeder.get_power(load_name)               # Get the real and reactive power of circuit element
feeder.set_power(load_name, p=100, q=50)  # Set the real and reactive power of circuit element
feeder.get_property(load_name, 'kV')      # Get a property of a circuit element (base voltage)
feeder.get_circuit_info()                 # Returns a dictionary of circuit info (total power, losses, etc.)
```

Additional commands and usage information are provided in the `examples` folder.

Note: The wrapper assumes a standard sign notation that is different than OpenDSS.
Powers for all elements (including for PV, loads, and batteries) use the sign notation:

* Positive = Consuming power (e.g. battery charging)
* Negative = Generating power (e.g. battery discharging)

For details on OpenDSSDirect.py, see:

https://dss-extensions.org/OpenDSSDirect.py/

## License

Distributed under the BSD 3-Clause License. See `LICENSE` for more information.

## Contact

Michael Blonsky - <Michael.Blonsky@nrel.gov>
