# -*- coding: utf-8 -*-

"""
A hardware module for communicating with the fast counter FPGA.

Copyright (c) 2021, the qudi developers. See the AUTHORS.md file at the top-level directory of this
distribution and on <https://github.com/Ulm-IQO/qudi-iqo-modules/>

This file is part of qudi.

Qudi is free software: you can redistribute it and/or modify it under the terms of
the GNU Lesser General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

Qudi is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with qudi.
If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import numpy as np

from qudi.core.configoption import ConfigOption
from qudi.interface.fast_counter_interface import FastCounterInterface
from qudi.hardware.fpga_fastcounter.cronologic import xtdc4_interface as tt_interface


class FastCounterFPGACronologic(FastCounterInterface):
    """ Qudi module for an FPGA based FastCounter.

    Example config for copy-paste:

    fast_counter:
        module.Class: 'fpga_fastcounter.fast_counter_fpga_cronologic.FastCounterFPGACronologic'
        options:
            fpgacounter_channel_apd_0: 0
            fpgacounter_channel_apd_1: 1
            fpgacounter_channel_trigger: 2

    """

    # config options
    #_package_path = ConfigOption('counter_package_path', missing='error')
    #_fpgacounter_serial = ConfigOption('fpgacounter_serial', missing='error')
    _gated = ConfigOption(name = 'gated', missing='error')
    _channel_apd_0 = ConfigOption('fpgacounter_channel_apd_0', 0, missing='warn')
    #_channel_apd_1 = ConfigOption('fpgacounter_channel_apd_1', None) TODO: add in a second channel, and figure out how to choose between them
    _channel_trigger = ConfigOption('fpgacounter_channel_trigger', 2, missing='warn')
    _read_channel_dc_offset = ConfigOption('read_channel_dc_offset', 0.90)
    _ext_trig_dc_offset = ConfigOption('ext_trig_dc_offset', 0.90)
    _gated_readout_s_pulsed_measurement = ConfigOption('gated_readout_s_pulsed_measurement', 300e-9)
    _gated_readout_s_scanned_measurement = ConfigOption('gated_readout_s_scanned_measurement', 1e-3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Scan process parameters
        self._counter_manager = None
        self.pulsed = None
        self._tt = None # dummy placement for now, will get rid of
        self._min_binwidth_ps = 100
        self._read_channels =[]

    def on_activate(self):
        """ Connect and configure the access to the FPGA.
        """
        #sys.path.append(self._package_path)

        self._counter_manager = tt_interface.TT4Manager()
        self._counter_manager.initialize_tt4()

        self.log.info(
            f"Cronologic TimeTagger with s/n "
            f"{self._counter_manager.static.board_serial}"
            f" is connected."
        )
        self._counter_manager.configure()
        self._counter_manager.get_param_info()

        self._min_binwidth_ps = self._counter_manager.para.binsize

        self._number_of_gates = int(100)
        self._bin_width_ns = self._min_binwidth_ps / 1e3 #in ns
        self._read_channels = [self._channel_apd_0]
        self._do_tiger_start = True
        self._do_tiger_stops=False
        self._do_continuous=False
        self._read_window_ns = 1000
        self._ref_trig_freq_Hz = 1/(self._read_window_ns*1e-9)
        self._ref_trig_pulse_width_ns = 10

        self.configure(
            self._read_window_ns * 1e-9,
            self._number_of_gates)

        self.statusvar = 0

    def get_constraints(self):
        """ Retrieve the hardware constrains from the Fast counting device.

        @return dict: dict with keys being the constraint names as string and
                      items are the definition for the constraints.

         The keys of the returned dictionary are the str name for the constraints
        (which are set in this method).

                    NO OTHER KEYS SHOULD BE INVENTED!

        If you are not sure about the meaning, look in other hardware files to
        get an impression. If still additional constraints are needed, then they
        have to be added to all files containing this interface.

        The items of the keys are again dictionaries which have the generic
        dictionary form:
            {'min': <value>,
             'max': <value>,
             'step': <value>,
             'unit': '<value>'}

        Only the key 'hardware_binwidth_list' differs, since they
        contain the list of possible binwidths.

        If the constraints cannot be set in the fast counting hardware then
        write just zero to each key of the generic dicts.
        Note that there is a difference between float input (0.0) and
        integer input (0), because some logic modules might rely on that
        distinction.

        ALL THE PRESENT KEYS OF THE CONSTRAINTS DICT MUST BE ASSIGNED!
        """

        constraints = dict()

        # the unit of those entries are seconds per bin. In order to get the
        # current binwidth in seconds use the get_binwidth method.
        constraints['hardware_binwidth_list'] = [self._min_binwidth_ps/1e12]

        # TODO: think maybe about a software_binwidth_list, which will
        #      postprocess the obtained counts. These bins must be integer
        #      multiples of the current hardware_binwidth

        return constraints

    def on_deactivate(self):
        """ Deactivate the FPGA.
        """
        self.log.info(
            f"Cronologic TimeTagger with s/n "
            f"{self._counter_manager.static.board_serial}"
            f" is disconnected."
        )
        self._counter_manager.close_device()
        if self.module_state() == 'locked':
            self.stop_measure()
        self.pulsed = None

    def configure(self, read_window_s, number_of_gates=0): #TODO add configuration options to the def

        """ Configuration of the fast counter.

        #@param float record_length_s: Total length of the timetrace/each single
        #                               gate in seconds.
        @param float read_window_s: Length of the gate.
        @param int number_of_gates: optional, number of gates in the pulse
                                    sequence. Ignore for not gated counter.

        @return tuple(binwidth_ns, read_window_s, number_of_gates):
                    binwidth_ns: float the binwidth in nanoseconds
                    read_window_s: the actual length of each gate window
                    number_of_gates: the number of gated, which are accepted
        """
        self._number_of_gates = number_of_gates
        #self._record_length = int(record_length_s / bin_width_s)
        self._read_window_ns = read_window_s * 1e9
        self._ref_trig_freq_Hz = 1 / read_window_s
        self.statusvar = 1

        #self.pulsed = self._tt.Pulsed(
        #    self._record_length,
        #    int(np.round(self._bin_width*1000)),
        #    self._number_of_gates,
        #    self._channel_apd_0,
        #    self._channel_detect,
        #    self._channel_sequence
        #)

        self._counter_manager.load_tt4(
            read_channels=self._read_channels,
            read_channel_dc_offset=self._read_channel_dc_offset,
            ext_trig_dc_offset=self._ext_trig_dc_offset,
            do_tiger_start=self._do_tiger_start,
            do_tiger_stops=self._do_tiger_stops,
            do_continuous=self._do_continuous,
            read_window_ns=self._read_window_ns,
            ref_trig_freq_Hz=self._ref_trig_freq_Hz,
            ref_trig_pulse_width_ns=self._ref_trig_pulse_width_ns,
            )

        return self._bin_width_ns, read_window_s, number_of_gates #Might want to return more?

    def start_tiger(self):
        """ Start the internal triggering. """
        #self.module_state.lock()
        self._counter_manager.start_tiger()
        return 0

    def stop_tiger(self):
        """ Stop the internal triggering. """
        #self.module_state.lock()
        self._counter_manager.stop_tiger()
        return 0

    def start_measure(self):
        """ Start the fast counter. """
        self.module_state.lock()
        self._counter_manager.start_capture()
        self.statusvar = 2
        return 0

    def stop_measure(self):
        """ Stop the fast counter. """
        if self.module_state() == 'locked':
            self._counter_manager.stop_capture()
            self.module_state.unlock()
        self.statusvar = 1
        return 0

    def pause_measure(self):
        """ Pauses the current measurement.

        Fast counter must be initially in the run state to make it pause.
        """
        if self.module_state() == 'locked':
            self._counter_manager.pause_capture()
            self.statusvar = 3
        return 0

    def continue_measure(self):
        """ Continues the current measurement.

        If fast counter is in pause state, then fast counter will be continued.
        """
        if self.module_state() == 'locked':
            self._counter_manager.continue_capture()
            self.statusvar = 2
        return 0

    def is_gated(self):
        """ Check the gated counting possibility.

        Boolean return value indicates if the fast counter is a gated counter
        (TRUE) or not (FALSE).
        """
        return self._gated

    def read_counts(self, num_to_read):
        '''
        Fast function to read the length of each packet, which is the number
        of hits.

        This does not take into account any extended buffers, which will affect
        the returned number of hits. Use read_counts() for long measurements

        After tt4 has been initialized, loaded, and start_capture() called,
        this function will read the number of counts from each packet that
        is triggered, either internally (tiGeR) or externally.

        Params:
            # num_to_read: int
            #     The number of packets to record.
        Returns:
            return_counts: list
            #     List populated with the hit_counts from each packet read,
            # totaling the num-to_read
        '''

        return self._counter_manager.read_counts_internal(num_to_read)

    def get_data_trace(self):
        """ Polls the current timetrace data from the fast counter.

        @return numpy.array: 2 dimensional array of dtype = int64. This counter
                             is gated the the return array has the following
                             shape:
                                returnarray[gate_index, timebin_index]

        The binning, specified by calling configure() in forehand, must be taken
        care of in this hardware class. A possible overflow of the histogram
        bins must be caught here and taken care of.
        """
        info_dict = {'elapsed_sweeps': None,
                     'elapsed_time': None}  # TODO : implement that according to hardware capabilities
        return np.array(self.pulsed.getData(), dtype='int64'), info_dict


    def get_status(self):
        """ Receives the current status of the Fast Counter and outputs it as
            return value.

        0 = unconfigured
        1 = idle
        2 = running
        3 = paused
        -1 = error state
        """
        return self.statusvar

    def get_binwidth(self):
        """ Returns the width of a single timebin in the timetrace in seconds. """
        width_in_seconds = self._bin_width * 1e-9
        return width_in_seconds

