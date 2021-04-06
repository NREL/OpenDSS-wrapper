# OpenDSS-wrapper
Distribution system simulation python wrapper to connect OpenDSSDirect.py with a co-simulation

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
    - --editable=git+https://github.nrel.gov/SETO-foresee/OpenDSS-wrapper
```

For a particular branch (or version), change the last line to:

```
    - --editable=git+https://github.nrel.gov/SETO-foresee/OpenDSS-wrapper@<branch-name>
```

### Stand-alone Installation

For a stand-alone installation, run the `setup.py` file from the command line:

```
python setup.py install
```

## Usage

The OpenDSS wrapper makes it easy to call OpenDSS commands without knowing any details about
OpenDSS syntax. Some sample commands are provided below.

Note: The wrapper assumes a standard sign notation that is different than OpenDSS.
All powers (including for PV, loads, and batteries) use the sign notation:

* Positive = Consuming power (battery charging)
* Negative = Generating power (battery discharging)

### 