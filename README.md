# OpenDSS-wrapper
Distribution system simulation python wrapper to connect OpenDSSDirect.py with a co-simulation framework

The wrapper contains user-friendly functions for various OpenDSS commands:
* Getting and setting power
* Getting voltage for an element or a bus
* Solving in QSTS modes (with or without controls)
* Redirecting (loading) dss files
* Collecting results 
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

The OpenDSS wrapper makes it easy to call OpenDSS commands without knowing any details about
OpenDSS syntax. Some sample commands and usage are provided in the `examples` folder.

Note: The wrapper assumes a standard sign notation that is different than OpenDSS.
All powers (including for PV, loads, and batteries) use the sign notation:

* Positive = Consuming power (e.g. battery charging)
* Negative = Generating power (e.g. battery discharging)

For details on OpenDSSDirect.py, see:

https://dss-extensions.org/OpenDSSDirect.py/

## License

Distributed under the BSD 3-Clause License. See `LICENSE` for more information.

## Contact

Michael Blonsky - <Michael.Blonsky@nrel.gov>
