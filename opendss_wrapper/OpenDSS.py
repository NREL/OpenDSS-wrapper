import opendssdirect as dss
import numpy as np
import pandas as pd

ELEMENT_CLASSES = {
    'Load': dss.Loads,
    'PV': dss.PVsystems,
    'Generator': dss.Generators,
    'Line': dss.Lines,
    'Xfmr': dss.Transformers,
    'Capacitor': dss.Capacitors,
    'RegControl': dss.RegControls,  # Tap changer
    'CapControl': dss.CapControls,  # Capacitor control
}
LINE_CLASSES = ['Line', 'Xfmr', 'Capacitor']


class OpenDSSException(Exception):
    pass


class OpenDSS:
    def __init__(self, redirects, time_step, start_time, **kwargs):
        self.dss = dss

        # Run redirect files before main dss file
        print('DSS Compiling...')
        if not isinstance(redirects, list):
            redirects = [redirects]
        for redirect in redirects:
            self.redirect(redirect)

        # add constant loadshape to remove existing loadshapes
        self.run_command('New Loadshape.constant npts=1 interval=1 mult=1 qmult=1')

        # check if elements exist. If storage exists, save storage names
        self.includes_elements = {class_name: len(ELEMENT_CLASSES[class_name].AllNames()) > 0 for class_name in
                                  ['Load', 'PV', 'Generator']}
        storages = self.get_all_elements('Storage')
        if len(storages):
            self.includes_elements['Storage'] = True
            self.storage_names = storages.index.str.replace('Storage.', '').to_list()
        else:
            self.includes_elements['Storage'] = False
            self.storage_names = []

        # Set to QSTS Mode
        self.run_command('set mode=yearly')  # Set to QSTS mode
        # dss.Solution.Mode(2)  # should set mode to yearly?

        dss.Solution.Number(1)  # Number of Monte Carlo simulations
        day_of_year = start_time.timetuple().tm_yday - 1
        dss.Solution.Hour(day_of_year * 24 + start_time.hour)  # QSTS starting hour

        # Run, without advancing, then set step size
        dss.Solution.StepSize(0)
        self.run_dss()
        dss.Solution.StepSize(time_step.total_seconds())

        print(f'DSS Compiled Circuit: {dss.Circuit.Name()}')

    @staticmethod
    def run_command(cmd):
        status = dss.run_command(cmd)
        if status:
            print(f'DSS Status ({cmd}): {status}')

    def redirect(self, filename):
        print(f'DSS Running file: {filename}')
        self.run_command(f'Redirect "{filename}"')

    def run_dss(self, no_controls=False):
        try:
            if no_controls:
                status = dss.Solution.SolveNoControl()
            else:
                status = dss.Solution.Solve()
            if status:
                print(f'DSS Solve Status: {status}')

            if self.includes_elements['Storage']:
                dss.Circuit.UpdateStorage()

        except Exception as e:
            self.run_command('export Eventlog')
            raise e

    # GENERAL GET METHODS

    @staticmethod
    def get_all_buses():
        return dss.Circuit.AllBusNames()

    @staticmethod
    def get_all_elements(element='Load'):
        if element in ELEMENT_CLASSES:
            cls = ELEMENT_CLASSES[element]
            df = dss.utils.to_dataframe(cls)
        else:
            df = dss.utils.class_to_dataframe(element, transform_string=lambda x: pd.to_numeric(x, errors='ignore'))
            # df = dss.utils.class_to_dataframe(element)
        return df

    @staticmethod
    def get_circuit_power(total=True):
        # returns negative of circuit power (positive = consuming power)
        powers = dss.Circuit.TotalPower()
        if len(powers) == 2:
            p, q = tuple(powers)
            p, q = -p, -q
        elif len(powers) == 6:
            p = powers[0:2:]
            q = powers[1:2:]
        else:
            raise OpenDSSException('Expected 1- or 3-phase circuit')
        if np.isnan(p) or np.isnan(q):
            raise OpenDSSException(f'NaN output for circuit power: ({p}, {q})')

        if total and isinstance(p, list):
            return sum(p), sum(q)
        else:
            return p, q

    @staticmethod
    def get_losses():
        p, q = dss.Circuit.Losses()
        return p / 1000, q / 1000

    def get_total_power(self, element='Load'):
        p_total, q_total = 0, 0

        if element in ELEMENT_CLASSES:
            cls = ELEMENT_CLASSES[element]
            all_names = cls.AllNames()
            for name in all_names:
                p, q = self.get_power(name, element, total=True)
                p_total += p
                q_total += q
        elif element == 'Storage' and self.includes_elements['Storage']:
            # reversing sign for storage
            storage_p = [-self.get_property(name, 'kW', 'Storage') for name in self.storage_names]
            storage_q = [-self.get_property(name, 'kvar', 'Storage') for name in self.storage_names]
            p_total = sum(storage_p)
            q_total = sum(storage_q)

        return p_total, q_total

    def get_circuit_info(self):
        # TODO: Add powers by phase if 3-phase; options to add/remove element classes
        p_total, q_total = self.get_circuit_power()
        p_loss, q_loss = self.get_losses()
        total_by_class = {class_name: self.get_total_power(class_name) for class_name, included in
                          self.includes_elements.items() if included}

        out = {'Total P (MW)': p_total / 1000,
               'Total Loss P (MW)': p_loss / 1000,
               }
        for class_name, (p, q) in total_by_class.items():
            out[f'Total {class_name} P (MW)'] = p / 1000

        out.update({'Total Q (MVAR)': q_total / 1000,
                    'Total Loss Q (MVAR)': q_loss / 1000,
                    })
        for class_name, (p, q) in total_by_class.items():
            out[f'Total {class_name} Q (MVAR)'] = q / 1000

        return out

    # VOLTAGE METHODS

    @staticmethod
    def get_bus_voltage(bus, phase=None, pu=True, polar=True, mag_only=True, average=False, zero_voltage_error=False):
        dss.Circuit.SetActiveBus(bus)

        if polar:
            if pu:
                v = dss.Bus.puVmagAngle()
            else:
                v = dss.Bus.VMagAngle()
        else:
            if pu:
                v = dss.Bus.PuVoltage()
            else:
                v = dss.Bus.Voltages()

        if any([np.isnan(x) for x in v]):
            raise OpenDSSException(f'NaN output for bus voltage: {bus}')

        n_phases = dss.Bus.NumNodes()
        assert len(v) // 2 == n_phases
        real_or_mag = tuple(v[0:2 * n_phases:2])  # real or magnitude
        imag_or_ang = tuple(v[1:2 * n_phases + 1:2])  # imaginary or angle

        if polar and zero_voltage_error and any([mag <= 1e-10 for mag in real_or_mag]):
            raise OpenDSSException(f'Bus "{bus}" voltage is out of bounds: {real_or_mag}')


        # if phase selected, only keep voltages from given phase
        if n_phases == 1:
            if polar and mag_only:
                return real_or_mag[0]
            else:
                return real_or_mag[0], imag_or_ang[0]
        elif phase is None:
            if polar and mag_only and average:
                return sum(real_or_mag) / len(real_or_mag)
            elif polar and mag_only:
                return real_or_mag
            else:
                return real_or_mag, imag_or_ang
        elif phase - 1 in range(n_phases):
            if polar and mag_only:
                return real_or_mag[phase - 1]
            else:
                return real_or_mag[phase - 1], imag_or_ang[phase - 1]
        else:
            raise OpenDSSException(f'Bad phase for {n_phases}-phase Bus {bus}: {phase}')

    @staticmethod
    def set_element(name, element):
        # dss.Circuit.SetActiveElement(self.__Class + '.' + self.__Name)
        name = name.lower()
        if element in ELEMENT_CLASSES:
            cls = ELEMENT_CLASSES[element]
        else:
            dss.Circuit.SetActiveClass(element)
            cls = dss.ActiveClass
        cls.Name(name)

        if cls.Name() != name:
            raise OpenDSSException(f'{element} "{name}" does not exist')

    def get_voltage(self, name, element='Load', line_bus=1, **kwargs):
        # note: for lines/transformers, always takes voltage from Bus1
        self.set_element(name, element)
        buses = dss.CktElement.BusNames()
        assert len(buses) == 2 if element in LINE_CLASSES else 1
        bus = buses[line_bus - 1 if element in LINE_CLASSES else 0]
        if dss.CktElement.NumPhases() == 1:
            kwargs['phase'] = 1
        return self.get_bus_voltage(bus, **kwargs)

    def get_all_bus_voltages(self, **kwargs):
        # gets all bus voltages, by phase
        buses = self.get_all_buses()

        data = {}
        for bus in buses:
            v = self.get_bus_voltage(bus, **kwargs)
            if isinstance(v, tuple):
                data.update({bus + '.' + str(i + 1): v_ph for i, v_ph in enumerate(v)})
            else:
                data[bus] = v
        return data

    # POWER METHODS

    def get_power(self, name, element='Load', phase=None, total=False, line_bus=1, raw=False):
        # Note: Returns power with the sign convention: positive=consuming

        # Returns the current power of the element/line (note line used for lines and xfmrs)
        #  - If raw==True: returns raw data from dss.CktElement.Powers(), as tuple
        #  - If 1-ph element: returns (P, Q) tuple
        #  - If 3-ph element: returns ((Pa, Pb, Pc), (Qa, Qb, Qc)) tuple, or (P, Q) if phase is specified or total==True
        #  - If 1-ph line: returns (P, Q) tuple of first bus (second bus if line_bus==2)
        #  - If 3-ph line: returns ((Pa, Pb, Pc), (Qa, Qb, Qc)) tuple, or (P, Q) if phase is specified or total==True
        self.set_element(name, element)
        powers = dss.CktElement.Powers()

        if raw:
            return tuple(powers)

        n_phases = dss.CktElement.NumPhases()
        if element in LINE_CLASSES:
            # remove zeros and second bus
            start = (line_bus - 1) * len(powers) // 2
            powers = powers[start: start + 2 * n_phases]
        else:
            # remove trailing zeros, if necessary
            powers = powers[:2 * n_phases]

        if n_phases == 1:
            return tuple(powers)
        elif n_phases in [2, 3]:
            if phase is None:
                p = tuple(powers[0:2 * n_phases:2])
                q = tuple(powers[1:2 * n_phases + 1:2])
                if total:
                    return sum(p), sum(q)
                else:
                    return p, q
            if phase - 1 in range(n_phases):
                powers = powers[(phase - 1) * 2: phase * 2]
                return tuple(powers)
            else:
                raise OpenDSSException(f'Unknown phase for {element} {name}: {phase}')
        else:
            raise OpenDSSException(f'Cannot parse powers for {element} {name}, num phases={n_phases}')

    def set_power(self, name, p=None, q=None, element='Load', size=None):
        if element in ELEMENT_CLASSES:
            self.set_element(name, element)
            cls = ELEMENT_CLASSES[element]
            if p is not None:
                cls.kW(p)
            if q is not None:
                cls.kvar(q)
        elif element == 'Storage':
            if p == 0:
                self.run_command(f'edit {element}.{name} kW=0 kvar=0 State=Idling')
                return

            if size is None:
                size = self.get_property(name, 'kWrated', element='Storage')
            if q is None:
                q = 0
            # calculate power factor and percent charge/discharge
            pf = np.cos(np.arctan(q / p))
            if p * q < 0:
                pf = -pf  # negative PF when P and Q are opposite sign
            p_pct = abs(p) / size * 100

            if p < 0:
                self.run_command(
                    f'edit {element}.{name} %discharge={p_pct:.4} pf={pf:.4} State=Discharging')
            else:
                self.run_command(f'edit {element}.{name} %charge={p_pct:.4} pf={pf:.4} State=Charging')
        else:
            raise OpenDSSException("Unknown element class:", element)

    def get_current(self, name, element='Load', polar=True, mag_only=True, line_bus=1, phase=None, total=False,
                    raw=False):
        # By default, returns current magnitudes for each phase (scalar for 1-phase, tuple for 3 phase). Options:
        #  - If mag_only=False, returns tuple of (magnitude, angle)
        #  - If polar=False, returns tuple of (real, imag)
        #  - If line_bus=2: returns currents for 2nd bus for lines and transformers
        #  - If phase is set (1, 2 or 3), only returns a scalar/tuple for that phase. Default is a tuple of all phases
        #  - If total=True, retuns a sum of all current magnitudes (only if polar & mag_only & phase=None)
        #  - If raw==True: returns raw data from dss.CktElement.CurrentsMagAng or dss.CktElement.Currents
        self.set_element(name, element)
        if polar:
            currents = dss.CktElement.CurrentsMagAng()
        else:
            currents = dss.CktElement.Currents()
        if raw:
            return tuple(currents)

        n_phases = dss.CktElement.NumPhases()
        if element in LINE_CLASSES:
            # remove zeros and second bus
            start = (line_bus - 1) * len(currents) // 2
            currents = currents[start: start + 2 * n_phases]
        else:
            # remove trailing zeros, if necessary
            currents = currents[:2 * n_phases]
        real_or_mag = tuple(currents[0:2 * n_phases:2])  # real or magnitude
        imag_or_ang = tuple(currents[1:2 * n_phases + 1:2])  # imaginary or angle

        if n_phases == 1:
            if polar and mag_only:
                return real_or_mag[0]
            else:
                return real_or_mag[0], imag_or_ang[0]
        elif n_phases in [2, 3]:
            if phase is None:
                if polar and mag_only:
                    if total:
                        return sum(real_or_mag)
                    else:
                        return real_or_mag
                else:
                    return real_or_mag, imag_or_ang
            if phase - 1 in range(n_phases):
                return real_or_mag[phase - 1], imag_or_ang[phase - 1]
            else:
                raise OpenDSSException(f'Unknown phase for {element} {name}: {phase}')
        else:
            raise OpenDSSException(f'Cannot parse currents for {element} {name}, num phases={n_phases}')

    def get_all_complex(self, name, element='Load'):
        self.set_element(name, element)
        return {
            'Voltages': dss.CktElement.Voltages(),
            'VoltagesMagAng': dss.CktElement.VoltagesMagAng(),
            'Currents': dss.CktElement.Currents(),
            'CurrentsMagAng': dss.CktElement.CurrentsMagAng(),
            'Powers': dss.CktElement.Powers(),
        }

    # PROPERTY METHODS

    def get_all_properties(self, name, element='Load'):
        self.set_element(name, element)
        all_properties = dss.Element.AllPropertyNames()
        return all_properties

    def get_property(self, name, property_name, element='Load'):
        all_properties = self.get_all_properties(name, element)
        if property_name not in all_properties:
            raise OpenDSSException(f'Could not find {property_name} property for {element} "{name}"')

        idx = all_properties.index(property_name)
        value = dss.Properties.Value(str(idx + 1))

        try:
            number = float(value)
            return number
        except ValueError:
            return value

    def set_property(self, name, property_name, value, element='Load'):
        self.set_element(name, element)
        all_properties = dss.Element.AllPropertyNames()
        if property_name not in all_properties:
            raise OpenDSSException(f'Could not find {property_name} property for {element} "{name}"')

        idx = all_properties.index(property_name)
        dss.Properties.Value(str(idx + 1), str(value))

        new_value = self.get_property(name, property_name, element)
        assert new_value == value

    def remove_loadshape(self, name, element='Load'):
        self.set_property(name, 'yearly', 'constant', element)

    def set_is_open(self, name, open=True, element='Load', term=0, phase=0):
        # term = dss.PDElements.FromTerminal()
        # phase = int(dss.CktElement.BusNames()[1].split(".")[1])
        self.set_element(name, element)
        if open:
            dss.CktElement.Open(term, phase)
        else:
            dss.CktElement.Close(term, phase)

    def get_is_open(self, name, element='Load', term=0, phase=0):
        # term = dss.PDElements.FromTerminal()
        # phase = int(dss.CktElement.BusNames()[1].split(".")[1])
        self.set_element(name, element)
        is_open = bool(dss.CktElement.IsOpen(term, phase))
        return is_open

    def set_tap(self, name, tap, max_tap=16):
        self.set_element(name, 'RegControl')
        tap = int(min(max(tap, -max_tap), max_tap))
        dss.RegControls.TapNumber(tap)

    def get_tap(self, name):
        self.set_element(name, 'RegControl')
        return int(dss.RegControls.TapNumber())

    def set_pt_ratio(self, name, pt_ratio):
        self.set_element(name, 'CapControl')
        dss.CapControls.PTRatio(pt_ratio)

    def get_pt_ratio(self, name):
        self.set_element(name, 'CapControl')
        return float(dss.CapControls.PTRatio())

