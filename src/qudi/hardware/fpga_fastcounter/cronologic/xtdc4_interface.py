# -*- coding: utf-8 -*-
"""
This file enables the functions from the xtdc4.dll library to be used
to control the cronologic TimeTagger4. It relies on the Python library: ctypes

More information about the TimeTagger4 can be found from cronologic's website:
    https://www.cronologic.de/product/timetagger
    
This python file must either be in the same folder as the xtdc4.dll or the path
must be editted to direct to the xtdc4.dll.

This file contains thhee following:
    - Constants that are unique to the TimeTagger4 product and used in the Class
    - Structures of variable types used in the dll
    - Class TT4Manager, which an instance should be used for the device(s) being
        used to handle the initialization, configuration, and measuring. Inside
        this class are added functions t ouse the TT4, such as completely 
        initializing a device, and configuring the read and write channels 
        for a measurement

Created on Mon Sep 25 10:45:20 2023

@author: agard
"""

import ctypes
import os
from pathlib import Path
# import time
import math


# place dll in a folder C:\Users\name\anaconda3\envs\qudi-env\Lib\site-packages\cronologic

# cwd is C:\Users\user\anaconda3\envs\qudi-env\Lib\site-packages\qudi


#%% make sure dll is in same file as interface

parent_dir = os.path.split(os.getcwd())[0]  # gets directory of cwd
os.add_dll_directory(parent_dir / Path('cronologic'))  # goes into folder cronologic
    
#%% Constants

# Error codes are set to this value if there has been no error
TIMETAGGER4_OK = 0

# auto trigger period
# 4 kHz for TimeTagger4-1G/2G (base frequency 250 MHz)
# 5 kHz for TimeTagger4-1.25G/2.5G/5G/10G (base frequency 312.5 MHz)
TIMETAGGER4_DEFAULT_AUTO_TRIGGER_PERIOD = 62500
        
# current version of the API
TIMETAGGER4_API_VERSION = 1
        
# The number of TDC input channels.
TIMETAGGER4_TDC_CHANNEL_COUNT = 4

# The number of timing generators. One for each TDC input and one for
# the Start input.
TIMETAGGER4_TIGER_COUNT = 5
        
# unsupported for TimeTagger4
TIMETAGGER4_LOWRES_CHANNEL_COUNT = 3
        
#  The number of potential trigger sources for the timing generators.
TIMETAGGER4_TRIGGER_COUNT = 16
        
# buffertype: either allocated (only option currently) or physical
TIMETAGGER4_BUFFER_ALLOCATE = 0
TIMETAGGER4_BUFFER_USE_PHYSICAL = 1
        
# Device types
CRONO_DEVICE_HPTDC = 0x1
CRONO_DEVICE_NDIGO5G = 0x2
CRONO_DEVICE_NDIGO250M = 0x4
CRONO_DEVICE_xTDC4 = 0x6
CRONO_DEVICE_TIMETAGGER4 = 0x8
CRONO_DEVICE_XHPTDC8 = 0xC
CRONO_DEVICE_NDIGO6 = 0xD
        
# %% Structures

class timetagger4_init_parameters(ctypes.Structure):
    '''
    Defines the timetagger4_init_parameters, which must be initialized before 
    using the device.
    
    fields:
        version: int
            The API version number
        card_index: int
            The index in the list of TimeTagger4 boards that 
            should be initialized.
        board_id: int
            the global index in all cronologic devices on this computer
        buffer_size: int64*8
            The minimum size of the DMA buffer (only the first index
             is used for TimeTagger4 devices)
        buffer_type: int
            The type of buffer. Must be set to 0.
        buffer_address: unint64
            This is set by timetagger4_init() to the start 
            address of the reserved memory
        variant: int
            Set to 0. Can be used to activate future device variants 
            such as different base frequencies
        device_type: int
            A constant for the different devices of cronologic CRONO_DEVICE_*.
        dma_read_delay: int
            The update delay of the write pointer after a packet 
            has been sent over PCIe. Specified in multiples of 16 ns. 
            Should not be changed by the user.
        use_ext_clock: int
            If set to 1 use external 10 MHz reference. If set to 0 
            use internal reference.
        rclk_sel: int
            Sets THS788 RClk frequency, default is 150 MHz.
    '''
    _fields_=[("version",ctypes.c_int),
              ("card_index",ctypes.c_int),
              ("board_id",ctypes.c_int),
              ("buffer_size", ctypes.c_int64*8), 
              ("buffer_type", ctypes.c_int),
              ("buffer_address", ctypes.c_uint64),
              ("variant", ctypes.c_int),
              ("device_type", ctypes.c_int),
              ("dma_read_delay", ctypes.c_int),
              ("use_ext_clock", ctypes.c_int),   
              ("rclk_sel", ctypes.c_int)
              ]
    
class timetagger4_static_info(ctypes.Structure):
    '''
    Define the timetagger4_static_info that contains information about the 
    board that does not change during run time.
    
    fields:
        size: int
            The number of bytes occupied by the structure.
        version: int
            A version number that is increased when the definition of the 
            structure is changed.
        board_id: int
            ID of the board
        driver_revision: int
            Encoded version number for the driver.
        driver_build_revision: int
            Build number of the driver according to cronologic’s internal 
            versioning system
        firmware_revision: int
            Revision number of the FPGA configuration.
        board_revision: int
            Describes the schematic configuration of the board
        subversion_revision: int
            Subversion revision id of the FPGA configuration source code
        chip_id: int
            reserved
        board_serial: int
            Serial number of the board
        flash_serial_high: uint
            64-bit manufacturer serial number of the flash chip
        flash_serial_low: uint
            64-bit manufacturer serial number of the flash chip
        flash_valid: ubyte
            If not 0 the driver found valid calibration data in the flash on 
            the board and is using it. This value is not applicable for the TimeTagger4
        calibration_date: char *20
            20-length char describing the time when the card was calibrated.
        bitstream_date: char *20
            20-length char describing the time when the bitstream on the card
        delay_bin_size: double
            Bin size of delay in ps
        auto_trigger_ref_clock: double
            The clock frequency of the auto trigger in Hz used for calculating 
            the auto_trigger_period
        rollover_period: uint32
            The number of bins in a rollover period. This is a power of two 
            (the maximum value of a hit timestamp is this value minus -1)
    '''
    _fields_=[("size",ctypes.c_int),
              ("version",ctypes.c_int),
              ("board_id",ctypes.c_int),
              ("driver_revision", ctypes.c_int), 
              ("driver_build_revision", ctypes.c_int),
              ("firmware_revision", ctypes.c_int),
              ("board_revision", ctypes.c_int),
              ("board_configuration", ctypes.c_int),
              ("subversion_revision", ctypes.c_int),
              ("chip_id", ctypes.c_int),         
              ("board_serial", ctypes.c_int),     
              ("flash_serial_low", ctypes.c_uint),
              ("flash_serial_high", ctypes.c_uint),
              ("flash_valid", ctypes.c_uint),
              ("calibration_date", ctypes.c_char*20),   
              ("bitstream_date", ctypes.c_char*20),  
              ("delay_bin_size", ctypes.c_double), 
              ("auto_trigger_ref_clock", ctypes.c_double), # 1/3.2 ns 
              ("rollover_period", ctypes.c_uint32),                 
              ]
    
class timetagger4_param_info(ctypes.Structure):
    '''
    Define the timetagger4_param_info that  contains information that changes 
    indirectly due to configuration changes.
    
    fields:
        size: int
            The number of bytes occupied by the structure.
        version: int
            A version number that is increased when the definition of the 
            structure is changed.
        binsize: double
            Bin size (in ps) of the measured TDC data.
        board_id: int
            Board ID
        channels: int
            Number of TDC channels of the board: 4
        channel_mask: int
            Bit assignment of each enabled input channel.
        total_buffer: int64
            The total amount of DMA buffer in bytes
        packet_binsize: double
            For TimeTagger4 the packet binsize is equal to the binsize and 
            depends on the Generation of the card. Gen 2: 100 ps
        quantisation: double
            Quantisation or measurement resolution.  Depending on the board 
            variant this ranges from 100 ps to 1000 ps.       
    '''
    _fields_=[("size",ctypes.c_int),
              ("version",ctypes.c_int),
              ("binsize", ctypes.c_double),
              ("board_id",ctypes.c_int),
              ("channels", ctypes.c_int),
              ("channel_mask", ctypes.c_int),
              ("total_buffer", ctypes.c_int64),
              ("packet_binsize", ctypes.c_double),
              ("quantisation", ctypes.c_double),             
              ]
    
class timetagger4_fast_info(ctypes.Structure):
    '''
    Define the timetagger4_fast_info that can be obtained within a few microseconds 
    
    fields:
        size: int
            The number of bytes occupied by the structure.
        version: int
            A version number that is increased when the definition of the 
            structure is changed.
        tdc_rpm: int
            Speed of the TDC fan in rounds per minute. Reports 0 if no fan is present.
        fpga_rpm: int
            Speed of the FPGA fan in rounds per minute. Reports 0 if no fan is present.
        alerts: int
            Alert bits from the temperature sensor and the system monitor. 
            The TimeTagger4 does not implement any temperature alerts
        pcie_pwr_mgmt: int
            always 0
        pcie_link_width: int
            Number of PCIe lanes the card uses. Should always be 1 for the TimeTagger4
        pcie_max_payload: int
            Maximum size in bytes for one PCIe transaction. 
            Depends on system configuration.
    '''
    _fields_=[("size",ctypes.c_int),
              ("version",ctypes.c_int),
              ("tdc_rpm", ctypes.c_int),
              ("fpga_rpm",ctypes.c_int),
              ("alerts", ctypes.c_int),
              ("pcie_pwr_mgmt", ctypes.c_int),
              ("pcie_link_width", ctypes.c_int),
              ("pcie_max_payload", ctypes.c_int),             
              ]
    
class timetagger4_trigger(ctypes.Structure):
    '''
    For each input, this structure determines whether rising or falling edges 
    on the inputs create trigger events for the TiGer blocks.
    
    fields:
        falling: ubyte
        rising: ubyte
           Select for which edges a trigger event is created inside the FPGA. 
           Set the corresponding flag for one of the edges or both edges when 
           using the input with a TiGer.
    '''
    _fields_=[("falling", ctypes.c_ubyte),
              ("rising", ctypes.c_ubyte)]
    
class timetagger4_tiger_block(ctypes.Structure):
    '''
    For each output channel, this structure configures the output pulse timing
    generator that is available for the TimeTagger4.
    
    fields:
        enable: ubyte
            Activates the timing generator (TiGer).
        negate: ubyte
            Inverts output polarity. Default is set to false.
        retrigger: ubyte:
            Enables retrigger setting.
            If enabled the timer is reset to the value of the start parameter,
            whenever the input signal is set while waiting to reach the stop time.
        extend: ubyte
            Not implemented.
        enable_lemo_output: ubyte
            Enables the LEMO output.This is DC coupled, so make sure that you 
            do not have any devices connected as inputs. 
        start: uint32
        stop: uint32
            The time during which the TiGer output is set, relative to the 
            trigger input. For Gen 2 devices, multiples of 3.2 ns
        sources: int
            A bit mask with a bit set for all trigger sources that can trigger 
            this TiGer block. Default is TAGGER4_TRIGGER_SOURCE_S        
    '''
    _fields_=[("enable", ctypes.c_ubyte),
              ("negate", ctypes.c_ubyte),
              ("retrigger", ctypes.c_ubyte),
              ("extend", ctypes.c_ubyte),
              ("enable_lemo_output", ctypes.c_ubyte),
              ("start", ctypes.c_uint32),
              ("stop", ctypes.c_uint32),
              ("sources", ctypes.c_int)]
    
class timetagger4_channel(ctypes.Structure):
    '''
    For each input channel, this structure contains the TDC channel settings.
    
    fields:
        enabled: ubyte
            Enable the TDC channel.
        rising: ubyte
            Not applicable for TimeTagger4. Rising and/or falling edge are 
            configured using the timetagger4_trigger structure. 
        cc_enable: ubyte
            Enable carry chain TDC as backup (not used for TimeTagger4)
        cc_same_edge: ubyte
            Set whether the carry chain TDC records the sameedge as THS788 
            (as backup) or opposite edge (not used for TimeTagger4)
        ths788_disable: ubyte
            Disable THS788 timestamps (not used for TimeTagger4)
        start: uint32
        stop: uint32
            Veto function for grouping of hits into packets in multiples of 
            the binsize. Only hits between start and stop are read out.
    '''
    _fields_=[("enabled", ctypes.c_ubyte),
              ("rising", ctypes.c_ubyte),
              ("cc_enable", ctypes.c_ubyte),
              ("cc_same_edge", ctypes.c_ubyte),
              ("ths788_disable", ctypes.c_ubyte),
              ("start", ctypes.c_uint32),
              ("stop", ctypes.c_uint32)]
    
class timetagger4_lowres_channel(ctypes.Structure):
    '''
    Contains digital channel settings. Not used in TimeTagger4
    
    fields:
        enabled: ubyte
            Enable TDC channel
        start: uint32
            only timestamps >= start are recorded
        stop: uint32
            only timestamps <= stop are recorded
    '''
    _fields_=[("enabled", ctypes.c_ubyte),
              ("start", ctypes.c_uint32),
              ("stop", ctypes.c_uint32)]
    
class timetagger4_delay_config(ctypes.Structure):
    '''
    Contains configurable delay value for each channel
    
    fields:
        delay: uint32
            Delay in static_info.delay_bin_size (currently 200 ps) for a channel.
            The value must be 0 <= delay <= 1023
    '''
    _fields_=[("delay", ctypes.c_uint32)]
    
class timetagger4_configuration(ctypes.Structure):
    '''
    This is the structure containing the configuration information for the device
    and the channels
    
    fields:
        size: int
            The number of bytes occupied by the structure.
        version: int
            A version number that is increased when the definition of the 
            structure is changed.
        tdc_mode: int
            TDC mode. Can be grouped or continuous by values of 
            TIMETAGGER4_TDC_MODE_GROUPED or TIMETAGGER4_TDC_MODE_CONTINUOUS, 
            respectively 
        start_rising: ubyte
            Not applicable for the TimeTagger4. Rising and/or falling edge are 
            configured using the timetagger4_trigger structure
        dc_offset: double*(TIMETAGGER4_TDC_CHANNEL_COUNT+1)
            Set the threshold voltage for the input channels S, A …D
            The supported range is −1.32 V to 1.18 V. This should be close to 
            50 % of the height of the input pulse.
        trigger: timetagger4_trigger*TIMETAGGER4_TRIGGER_COUNT
            Configuration of the polarity of the external trigger sources.
        tiger_block: timetagger4_tiger_block*TIMETAGGER4_TIGER_COUNT
            Configuration of the timing generators
        channel: timetagger4_channel*TIMETAGGER4_TDC_CHANNEL_COUNT
            Configuration for the TDC channels
        lowres_channel: timetagger4_lowres_channel*TIMETAGGER4_LOWRES_CHANNEL_COUNT
            Not applicable for TimeTagger4.
        auto_trigger_period: uint32
        auto_trigger_random_exponent: uint32
            Create a trigger either periodically or randomly.
        delay_config: timetagger4_delay_config*(TIMETAGGER4_TDC_CHANNEL_COUNT+1)
            Configuration of the channel delay values
    '''
    _fields_=[("size",ctypes.c_int),
              ("version",ctypes.c_int),
              ("tdc_mode",ctypes.c_int),
              ("start_rising", ctypes.c_ubyte),
              ("dc_offset", ctypes.c_double*(TIMETAGGER4_TDC_CHANNEL_COUNT+1)), 
              ("trigger", timetagger4_trigger*TIMETAGGER4_TRIGGER_COUNT),
              ("tiger_block", timetagger4_tiger_block*TIMETAGGER4_TIGER_COUNT),
              ("channel", timetagger4_channel*TIMETAGGER4_TDC_CHANNEL_COUNT),
              ("lowres_channel", timetagger4_lowres_channel*TIMETAGGER4_LOWRES_CHANNEL_COUNT),
              ("auto_trigger_period", ctypes.c_uint32),  
              ("auto_trigger_random_exponent", ctypes.c_uint32),
              ("delay_config", timetagger4_delay_config*(TIMETAGGER4_TDC_CHANNEL_COUNT+1))          
              ]
    
class timetagger4_read_in(ctypes.Structure):
    '''
    Defines the structure for the read in of packets and acknowledging their read
    
    fields:
        acknowledge_last_read: ubyte
            If set timetagger4_read() automatically acknowledges packets from 
            the last read. Otherwise timetagger4_acknowledge() needs to be 
            called explicitly by the user.
    '''
    _fields_=[("acknowledge_last_read",ctypes.c_ubyte)         
              ]
    
class crono_packet(ctypes.Structure):
    '''
    Defines the structure for packets
    
    fields:
        channel: uint8
            Index of the source channel of the data. 
            Pseudo channel 15 is used for rollovers
        card: uint8
            Identifies the source card in case there are multiple boards present. 
            Defaults to 0 if no value is assigned to the parameter board_id in 
            Structure timetagger4_init_parameters
        type: uint8
            The data stream consists of 32-bit unsigned data as signified by
            CRONO_PACKET_TYPE_32_BIT_UNSIGNED = 6 .
        flags: uint8
            Bit field of TIMETAGGER4 _PACKET_FLAG_* bits
        length: uint32
            Number of 64-bit elements (each containing up to 2 TDC hits) 
            in the data array. The number of hits contained is equal to 
            2 * length - (flags & PACKET_FLAG_ODD_HITS) ? 1 : 0.
        timestamp: uint64
            Coarse timestamp of the start pulse. Values are given in multiples 
            of packet_binsize contained in timetagger4_param_info.
        data: uint64*1
            Contains the TDC hits as a variable length array (length can be zero). 
            The user can cast the array to uint32_t* to directly operate on the 
            TDC hits.
    '''
    _fields_=[("channel",ctypes.c_uint8),      
              ("card",ctypes.c_uint8),
              ("type",ctypes.c_uint8),
              ("flags",ctypes.c_uint8),
              ("length",ctypes.c_uint32),
              ("timestamp",ctypes.c_int64),
              ("data",ctypes.c_uint64*1),
              ]
    
class timetagger4_read_out(ctypes.Structure):
    '''
    Defines the structure for the read out of packets
    
    fields:
        first_packet: pointer to crono_packet
            Pointer to the first packet that was captured by the call of 
            timetagger4_read().
        last_packet: pointer to crono_packet
            Address of header of the last packet in the buffer. 
            This packet is still valid, all data after this packet is invalid.
        error_code: int
            Assignments of the error codes CRONO_READ
        error_message: pointer to char
            The last error in human readable form, possibly with additional 
            information about the error.
    '''
    _fields_=[("first_packet",ctypes.POINTER(crono_packet)),
              ("last_packet",ctypes.POINTER(crono_packet)),   
              ("error_code",ctypes.c_int),   
              ("error_message", ctypes.c_char_p),   
              ]
    
class timetagger4_device(ctypes.Structure):
    '''
    Defined structure for the device pointer type. This structure is used by the
    TimeTagger4 code to interact with the device instance
    
    fields:
        timetagger4: void pointer
            a pointer to a void type to be used by xtdc4.dll
    '''
    _fields_ = [("timetagger4", ctypes.c_void_p)]
  


# %% TT4Manager 
    
class TT4Manager:
    '''
    Manager for a single TimeTagger4 device. 
    '''
    
    def __init__(self):
        '''
        Define a bunch of constants attributed to the tt4_manager
        
        And define the argtypes and restype for the functions
        '''
        self.dll_cronologic =       ctypes.cdll.xtdc4_driver_64   
        self.dll_python_functions = ctypes.cdll.xtdc4_python_functions_64 
        
        self.TIMETAGGER4_OK = 0
        
        self.TIMETAGGER4_TDC_MODE_GROUPED = 0
        self.TIMETAGGER4_TDC_MODE_CONTINUOUS = 1

        ### trigger index
        self.TIMETAGGER4_TRIGGER_S =0
        self.TIMETAGGER4_TRIGGER_A =1
        self.TIMETAGGER4_TRIGGER_B =2
        self.TIMETAGGER4_TRIGGER_C =3
        self.TIMETAGGER4_TRIGGER_D =4
        self.TIMETAGGER4_TRIGGER_AUTO =14
        self.TIMETAGGER4_TRIGGER_ONE =15
        
        ### trigger source
        self.TIMETAGGER4_TRIGGER_SOURCE_NONE =0x00000000 
        self.TIMETAGGER4_TRIGGER_SOURCE_S =0x00000001 
        self.TIMETAGGER4_TRIGGER_SOURCE_A =0x00000002 
        self.TIMETAGGER4_TRIGGER_SOURCE_B =0x00000004 
        self.TIMETAGGER4_TRIGGER_SOURCE_C =0x00000008 
        self.TIMETAGGER4_TRIGGER_SOURCE_D =0x00000010 
        self.TIMETAGGER4_TRIGGER_SOURCE_S1 =0x00000020 
        self.TIMETAGGER4_TRIGGER_SOURCE_S1 =0x00000040
        self.TIMETAGGER4_TRIGGER_SOURCE_GATE =0x00000080 
        self.TIMETAGGER4_TRIGGER_SOURCE_AUTO =0x00004000 
        self.TIMETAGGER4_TRIGGER_SOURCE_ONE =0x00008000 

        ### dc offsets
        #   These values should be half the actual pulse amplitude
        self.TIMETAGGER4_DC_OFFSET_P_NIM = 0.35
        self.TIMETAGGER4_DC_OFFSET_P_AD3 = 0.45
        self.TIMETAGGER4_DC_OFFSET_P_CMOS =1.18
        self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_33 =1.18
        self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_25 =1.18
        self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_18 =0.90
        self.TIMETAGGER4_DC_OFFSET_P_TTL =1.18
        self.TIMETAGGER4_DC_OFFSET_P_LVTTL_33 =1.18
        self.TIMETAGGER4_DC_OFFSET_P_LVTTL_25 =1.18
        self.TIMETAGGER4_DC_OFFSET_P_SSTL_3 =1.18
        self.TIMETAGGER4_DC_OFFSET_P_SSTL_2 =1.18
        self.TIMETAGGER4_DC_OFFSET_N_NIM =-0.35
        self.TIMETAGGER4_DC_OFFSET_N_CMOS =-1.32
        self.TIMETAGGER4_DC_OFFSET_N_LVCMOS_33 =-1.32
        self.TIMETAGGER4_DC_OFFSET_N_LVCMOS_25 =-1.25
        self.TIMETAGGER4_DC_OFFSET_N_LVCMOS_18 =-0.90
        self.TIMETAGGER4_DC_OFFSET_N_TTL =-1.32
        self.TIMETAGGER4_DC_OFFSET_N_LVTTL_33 =-1.32
        self.TIMETAGGER4_DC_OFFSET_N_LVTTL_25 =-1.25
        self.TIMETAGGER4_DC_OFFSET_N_SSTL_3 =-1.32
        self.TIMETAGGER4_DC_OFFSET_N_SSTL_2 =-1.25
        
        ### CRONO_READ errors:
        self.CRONO_READ_OK = 1
        self.CRONO_READ_NO_DATA = 2
        self.CRONO_READ_INTERNAL_ERROR = 3
        self.CRONO_READ_TIMEOUT = 4
        
        ### crono_packet flags
            
        # If this bit is set, the last data word in the data array consists of 
        # one timestamp only which is located in the lower 32 bits of the 64-bit 
        # data word (little endian)
        self.TIMETAGGER4_PACKET_FLAG_ODD_HITS = 1
        # Timestamp of a hit is above the range of 8-bit rollover number and 
        # 24-bit hit timestamp. The group is closed, all other hits are ignored
        self.TIMETAGGER4_PACKET_FLAG_SLOW_SYNC = 2
        # The trigger unit has discarded packets due to a full FIFO because the 
        # data rate is too high. Starts are missed and stops are potentially in wrong groups.
        self.TIMETAGGER4_PACKET_FLAG_START_MISSED = 4
        # The trigger unit has shortened the current packet due to a full 
        # pipeline FIFO because the data rate is too high. Stops are missing in
        # the current packet.
        self.TIMETAGGER4_PACKET_FLAG_SHORTENED = 8
        # The internal DMA FIFO was full. This is caused either because the 
        # data rate is too high on too many channels. Packet loss is possible
        self.TIMETAGGER4_PACKET_FLAG_DMA_FIFO_FULL = 16
        # The host buffer was full. Might result in dropped packets. 
        # This is caused either because the data rate is too high or by data 
        # not being retrieved fast enough from the buffer. Solutions are 
        # increasing buffer size if the overload is temporary or by avoiding or 
        # optimizing any additional processing in the code that reads the data
        self.TIMETAGGER4_PACKET_FLAG_HOST_BUFFER_FULL = 32
        
        # Define arg and res types of dll functions
        
        # self.get_default_init_parameters = self.dll_cronologic.timetagger4_get_default_init_parameters
        self.dll_cronologic.timetagger4_get_default_init_parameters.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_get_default_init_parameters.argtypes  = [
                                            ctypes.POINTER(timetagger4_init_parameters)
                                            ]
        
        # self._init = self.dll_cronologic.timetagger4_init
        self.dll_cronologic.timetagger4_init.restype = ctypes.POINTER(timetagger4_device)
        self.dll_cronologic.timetagger4_init.argtypes =                 [
                                            ctypes.POINTER(timetagger4_init_parameters),
                                            ctypes.POINTER(ctypes.c_int),
                                            ctypes.POINTER(ctypes.c_char_p)
                                            ]
        
        # self._get_static_info = self.dll_cronologic.timetagger4_get_static_info
        self.dll_cronologic.timetagger4_get_static_info.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_get_static_info.argtypes =      [
                                            ctypes.POINTER(timetagger4_device),
                                            ctypes.POINTER(timetagger4_static_info)
                                            ]
        
        # self._get_param_info = self.dll_cronologic.timetagger4_get_param_info
        self.dll_cronologic.timetagger4_get_param_info.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_get_param_info.argtypes =      [
                                            ctypes.POINTER(timetagger4_device),
                                            ctypes.POINTER(timetagger4_param_info)
                                            ]
        
        # self._get_fast_info = self.dll_cronologic.timetagger4_get_fast_info
        self.dll_cronologic.timetagger4_get_fast_info.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_get_fast_info.argtypes =      [
                                            ctypes.POINTER(timetagger4_device),
                                            ctypes.POINTER(timetagger4_fast_info)
                                            ]
        
        # self._get_default_configuration = self.dll_cronologic.timetagger4_get_default_configuration
        self.dll_cronologic.timetagger4_get_default_configuration.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_get_default_configuration.argtypes = [
                                                ctypes.POINTER(timetagger4_device), 
                                                ctypes.POINTER(timetagger4_configuration)
                                                ]   
        
        # self._configure = self.dll_cronologic.timetagger4_configure
        self.dll_cronologic.timetagger4_configure.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_configure.argtypes =            [
                                            ctypes.POINTER(timetagger4_device), 
                                            ctypes.POINTER(timetagger4_configuration)
                                            ]
        
        # self._start_capture = self.dll_cronologic.timetagger4_start_capture
        self.dll_cronologic.timetagger4_start_capture.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_start_capture.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
        
        # self._pause_capture = self.dll_cronologic.timetagger4_pause_capture
        self.dll_cronologic.timetagger4_pause_capture.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_pause_capture.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
        
        # self._continue_capture = self.dll_cronologic.timetagger4_continue_capture
        self.dll_cronologic.timetagger4_continue_capture.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_continue_capture.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
        
        # self._stop_capture = self.dll_cronologic.timetagger4_stop_capture
        self.dll_cronologic.timetagger4_stop_capture.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_stop_capture.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
            
        # self._acknowledge = self.dll_cronologic.timetagger4_acknowledge
        self.dll_cronologic.timetagger4_acknowledge.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_acknowledge.argtypes = [
                                            ctypes.POINTER(timetagger4_device),
                                            ctypes.POINTER(crono_packet)
                                            ]
        
        # self._read = self.dll_cronologic.timetagger4_read
        self.dll_cronologic.timetagger4_read.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_read.argtypes = [
                                            ctypes.POINTER(timetagger4_device),
                                            ctypes.POINTER(timetagger4_read_in),
                                            ctypes.POINTER(timetagger4_read_out)
                                            ]
        
        # self._start_tiger  = self.dll_cronologic.timetagger4_start_tiger 
        self.dll_cronologic.timetagger4_start_tiger.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_start_tiger.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
           
        # self._stop_tiger  = self.dll_cronologic.timetagger4_stop_tiger 
        self.dll_cronologic.timetagger4_stop_tiger.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_stop_tiger.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
        
        # self._get_last_err_message = self.dll_cronologic.timetagger4_get_last_error_message
        self.dll_cronologic.timetagger4_get_last_error_message.restype = ctypes.c_char_p
        self.dll_cronologic.timetagger4_get_last_error_message.argtypes = [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
            
        # self._close = self.dll_cronologic.timetagger4_close
        self.dll_cronologic.timetagger4_close.restype = ctypes.c_int
        self.dll_cronologic.timetagger4_close.argtypes =    [
                                            ctypes.POINTER(timetagger4_device)
                                            ]
    def chk(self, status):
        '''
        Function to check for an error, based off tt4 get_last_err_message function.
        Once a device has been initialized, this function can be used. If the 
        device has not been initialized yet (before running init()) use
        chk_no_device().
        
        Params:
            status: int
                Error code returned from other TT4Manager functions. If not 0, 
                then error occured and Exception will be raised
        '''
        if status is None or status != self.TIMETAGGER4_OK:
            err_message_bytes = self.get_last_err_message()
            raise Exception("Could not configure TimeTagger4: {}".format(err_message_bytes.decode()))
            self.close_device()
        else:
            return status   
    
    def chk_no_device(self):
        '''
        Function to check for an error code initially set to 0 and saved to the
        instance of the TT4Manager. Before a tt4 device is initialized, a 
        predefined error code is the only status to check. Once a device has 
        '''
        status = self.error_int.value
        print(status)
        if status is None or status != self.TIMETAGGER4_OK:
            err_mess_b = self.error_char_p.value
            raise Exception("Could not init TimeTagger4 compatible board: {}".format(err_mess_b.decode()))
        else:
            return status
    
    def init(self, buffer_size = 8 * 1024 * 1024):
        '''
        This function initialized the device and gets a device pointer to use
        for this instance of the TT4Manager.
        
        The card must be initialized first before reading data. The process is 
        to get the default init parameters and change some values. 
        E.g. choose one of multiple cards by the index or use a larger buffer.
    
        Params:
            buffer_size: int64
                The minimum size of the DMA buffer. If set to 0 the default 
                size of 16 MByte is used
        '''
        # Create a variable params based off the struct timetagger4_init_parameters
        self.params = timetagger4_init_parameters()
        self.dll_cronologic.timetagger4_get_default_init_parameters(ctypes.byref(self.params))
        self.params.buffer_size[0] = ctypes.c_int64(buffer_size)
        
        # Before a device pointer is created, the error is contained in a 
        # seperate variable. Once device pointer created, then we can call
        # error messages through device pointer
        self.error_int = ctypes.c_int()
        self.error_char_p = ctypes.c_char_p()
        
        # Initialize the Device 
        self.device_p = self.dll_cronologic.timetagger4_init(ctypes.byref(self.params), 
                                      ctypes.byref(self.error_int), 
                                      ctypes.byref(self.error_char_p))
        
        # self.chk_no_device()
        
    def get_static_info(self):
        '''
        Gets a structure that contains information about the board that does 
        not change during run time.
        '''
        # Create the static info 
        self.static = timetagger4_static_info()
        status = self.dll_cronologic.timetagger4_get_static_info(self.device_p, 
                                                      ctypes.byref(self.static))
        self.chk(status)
        
        return status
    
    
    def get_param_info(self):
        '''
        Gets a structure that contains information that changes indirectly 
        due to configuration changes
        '''
        # Create the param info 
        self.para = timetagger4_param_info()
        status = self.dll_cronologic.timetagger4_get_param_info(self.device_p, 
                                                     ctypes.byref(self.para))
        self.chk(status)
        
        return status
    
    def get_fast_info(self):
        '''
        This call gets a structure that contains dynamic information that can 
        be obtained within a few microseconds
        '''
        # Create the param info 
        self.fast = timetagger4_fast_info()
        status = self.dll_cronologic.timetagger4_get_fast_info(self.device_p, 
                                                    ctypes.byref(self.fast))
        self.chk(status)
        
        return status
    
    
    def get_default_configuration(self):
        '''
        Gets default configuration. Copies the default configuration to the 
        specified config pointer
        '''
        self.config = timetagger4_configuration()
        status = self.dll_cronologic.timetagger4_get_default_configuration(self.device_p, 
                                                    ctypes.byref(self.config))
        self.chk(status)
        
        return status
    
    def configure(self):
        '''
        Configures the timetagger4_manager.
        '''
        status = self.dll_cronologic.timetagger4_configure(self.device_p, 
                                    ctypes.byref(self.config))
        self.chk(status)
        
        return status
    
    def get_read_config(self, acknowledge_last_read_bool = True):
        '''
        Create instance of the read in structure. Use this read in instance
        to set whether the prev. read should be automatically acknowledged.
        
        Params:
            acknowledge_last_read_bool: bool
                If set timetagger4_read() automatically acknowledges packets 
                from the last read. Otherwise timetagger4_acknowledge() needs 
                to be called explicitly by the user.
        '''
        self.read_config = timetagger4_read_in()
        self.read_config.acknowledge_last_read = acknowledge_last_read_bool
        
    def get_read_data(self):
        '''
        Create an instance of the read out structure, which holds the crono_packets
        '''
        self.read_data = timetagger4_read_out()
        
    def acknowledge(self, packet_p):
        '''
        Acknowledges the processing of the last read block. This is only 
        necessary if timetagger4_read() is not called with in.acknowledge_last_read set
        '''
        status = self.dll_cronologic.timetagger4_acknowledge(self.device_p, packet_p)
        self.chk(status)
    
        return status
    
    def start_capture(self):
        '''
        Start data acquisition.
        '''
        status = self.dll_cronologic.timetagger4_start_capture(self.device_p)
        self.chk(status)
    
        return status
        
    def pause_capture(self):
        '''
        Pause a started data acquisition. Pause and continue have less overhead 
        than start and stop but don’t allow for a configuration change.
        '''
        status = self.dll_cronologic.timetagger4_pause_capture(self.device_p)
        self.chk(status)
    
        return status
    
    def continue_capture(self):
        '''
        Call this to resume data acquisition after a call to timetagger4_pause_capture().
        Pause and continue have less overhead than start and stop but don’t 
        allow for a configuration change.
        '''
        status = self.dll_cronologic.timetagger4_continue_capture(self.device_p)
        self.chk(status)
    
        return status
    
    def stop_capture(self):
        '''
        Stop data acquisition.
        '''
        status = self.dll_cronologic.timetagger4_stop_capture(self.device_p)
        self.chk(status)
    
        return status
    
    
    def read(self):
        '''
        Return a pointer to an array of captured data in read_out. 
        The result contains a batch of packets of type timetagger4_packet. 
        The batch is described by first_packet and last_packet in the 
        timetagger4_read_in structure .
        
        Returns an error code as defined in the structure timetagger4_read_out 
        (CRONO_ERROR) and the returned value should be used to check for errors
        
        
        '''
        status = self.dll_cronologic.timetagger4_read(self.device_p, ctypes.byref(self.read_config), 
                           ctypes.byref(self.read_data))    
        return status
    
    def start_tiger(self):
        '''
        Start the timing generator. 
        This can be done independently of the state of the data acquisition
        '''
        status = self.dll_cronologic.timetagger4_start_tiger(self.device_p)
        self.chk(status)
    
        return status
    
    def stop_tiger(self):
        '''
        Stop the timing generator.
        This can be done independently of the state of the data acquisition
        '''
        status = self.dll_cronologic.timetagger4_stop_tiger(self.device_p)
        self.chk(status)
    
        return status
    
    def get_last_err_message(self):
        '''
        Returns most recent error message
        '''
        ret_chr = self.dll_cronologic.timetagger4_get_last_error_message(self.device_p)
                
        return ret_chr
    
    def close_device(self):
        '''
        Closes the devices, releasing all resources.
        '''
        try:
            self.dll_cronologic.timetagger4_close(self.device_p)
            # print("Device closed properly")
        except Exception:
            print("Error: tt4_manager does not contain properly initialized device. Please restart kernel.")

    # Functions for working with TimeTagger4 not in original cronologic dll
    
    def initialize_tt4(self, buffer_size = 8 * 1024 * 1024):
        '''
        This function combines the inital steps to initialize and configure the
        TimeTagger4 device. The function first initializes the board and creates
        an instance of the device in the tt4_manager. Then the static info is created
        and used to get the default configuration for the device.
        
        Params:
            buffer_size: int64
                The minimum size of the DMA buffer. If set to 0 the default 
                size of 16 MByte is used
        Returns:
            tt4_manager.device_p: pointer to timetagger4_device
                the device pointer for the initialized device           
        '''
        self.init(buffer_size)
        self.get_static_info()
        self.get_default_configuration()
        
        return self.device_p
        
    def load_tt4(self,
                  read_channels = [],
                  read_channel_dc_offset = 1.0,
                  ext_trig_dc_offset = 1.0,
                  delay = 0, # ns
                  do_tiger_start = False, 
                  do_tiger_stops = False, 
                  do_continuous = False,
                  read_window_ns = 50000,
                  ref_trig_freq_Hz = 20000,
                  ref_trig_pulse_width_ns = 10,
                  tiger_ttl_source = 0x00004000 # TIMETAGGER4_TRIGGER_SOURCE_AUTO
):
        '''
        Function to load the timetagger4 for basic counting applications. Use
        this function to configure the channels to read from and the timing generator.
        
        Params:
            read_channels: list(int) = []
                List of ints of the channels to read from. Channel A -> 0, etc.
            read_channel_dc_offset: float = 1.0
                Dc offset voltage value for the read channels. 
            ext_trig_dc_offset: float = 1.0
                Dc offset voltage value input to expect from ext triggers
            do_tiger_start: bool = False
                if True, TiGer pulses will be used to start capture, at a frequency
                of ref_trig_freq_Hz. A physical output pulse with width ref_trig_pulse_width_ns
                will be generated
            do_tiger_stops: bool = False
                if True, TiGer pulses will be used to stop capture. 
                NOT IMPLIMENTED
            do_continuous: bool = False
                if True, continuous capture will be used
            read_window_ns: int = 50000
                Duration of the read window
            ref_trig_freq_Hz: int = 20000
                Frequency used for TiGer start pulse generation
            ref_trig_pulse_width_ns: int = 10
                Pulse width used for TiGer start pulse generation
        '''
        # make sure we have static info on the TT4Manager instance
        try:
            static = self.static
        except Exception:
            self.get_static_info()
            static = self.static
            
        # make sure we have config info on the TT4Manager instance
        try:
            config = self.config
        except Exception:
            self.get_default_configuration()
            config = self.config
            
        # Bin size, in ps, that the TT4 is quantized in.
        # This is in the param_info, but we need it before we call that info...
        binsize = 100 #ps
        
        # Adjust the readout_window to # of bins based on binsize (ps)
        read_window_bins = int(read_window_ns * (1000 / binsize))
        delay_bins = int(delay * (1000 / binsize))
        
        # set the config for each channel that will be read from 
        # CURRENTLY, WILL ONLY WORK WITH SINGLE CHANNEL READ
        for ch in read_channels:
            # enable recording of hits on this channel
            config.channel[ch].enabled = True
            
            #config.delay_config[ch+1].delay = ctypes.c_uint32(delay_bins)
            
            # define recording range for the channel
            config.channel[ch].start = ctypes.c_uint32(0 + delay_bins)
            if not do_continuous:
                config.channel[ch].stop = ctypes.c_uint32(read_window_bins + delay_bins)
            else: # set to max value
                config.channel[ch].stop = ctypes.c_uint32(0x7fffffff)
            
            # user can pass values saved in tt4_manager, like 2.5 V TTL pulse
            config.dc_offset[ch+1] = read_channel_dc_offset
            
            if do_tiger_stops:
               	# TiGer stops will be config'd to use positive pulses
                config.trigger[self.TIMETAGGER4_TRIGGER_A + ch].falling = False
                config.trigger[self.TIMETAGGER4_TRIGGER_A + ch].rising = True
            else:
                # for ext signals, rising vs falling config'd by passed dc offset
                if read_channel_dc_offset > 0:
                    config.trigger[self.TIMETAGGER4_TRIGGER_A + ch].falling = False
                    config.trigger[self.TIMETAGGER4_TRIGGER_A + ch].rising = True
                else:
                    config.trigger[self.TIMETAGGER4_TRIGGER_A + ch].falling = True
                    config.trigger[self.TIMETAGGER4_TRIGGER_A + ch].rising = False
        
        if do_tiger_start or do_continuous:
            # generate an internal trigger based on readout_window_ns, used for tiger and continuous mode
            tt4_period = int(static.auto_trigger_ref_clock / ref_trig_freq_Hz)
            config.auto_trigger_period = ctypes.c_uint32(tt4_period)
            config.auto_trigger_random_exponent = 0;
        
        # width of pulse used in the auto_trigger clock periods
        pulse_width = int(ref_trig_pulse_width_ns * 1e-9 * static.auto_trigger_ref_clock)
        
        ### TiGer set up
        # sending a signal to the LEMO outputs (and to the TDC on the same channel)
        # requires proper 50 Ohm termination on the LEMO output to work reliably
        if not do_continuous:
            config.tdc_mode = self.TIMETAGGER4_TDC_MODE_GROUPED
        
            # generate above configured auto trigger to generate a 
         	# signal with pulse width (def'd above) on LEMO output Start
            # By default, the output pulse is at +0.90 V
             
            if do_tiger_start:
                config.tiger_block[0].enable =  1
                config.tiger_block[0].enable_lemo_output = 1
                config.dc_offset[0] =  self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_18
                config.trigger[self.TIMETAGGER4_TRIGGER_S].falling = 0;
                config.trigger[self.TIMETAGGER4_TRIGGER_S].rising = 1;
                
            else:
                config.tiger_block[0].enable =  0
                config.tiger_block[0].enable_lemo_output = 0
            # TiGer starts will be config'd to use positive pulses
            
            config.tiger_block[0].start = 0
            config.tiger_block[0].stop = config.tiger_block[0].start + pulse_width
            config.tiger_block[0].negate = 0
            config.tiger_block[0].retrigger = 0
            config.tiger_block[0].extend = 0
            config.tiger_block[0].sources = tiger_ttl_source
            
            config.dc_offset[0] =  ext_trig_dc_offset
            
            if ext_trig_dc_offset > 0:
                config.trigger[self.TIMETAGGER4_TRIGGER_S].falling = 0;
                config.trigger[self.TIMETAGGER4_TRIGGER_S].rising = 1;
            else:
                config.trigger[self.TIMETAGGER4_TRIGGER_S].falling = 1;
                config.trigger[self.TIMETAGGER4_TRIGGER_S].rising = 0;       
        else:
         	# Auto trigger is used as a start signal
            config.tdc_mode = self.TIMETAGGER4_TDC_MODE_CONTINUOUS;
        
        # Now configure TiGeR stops, if enabled
        for i in range(1, TIMETAGGER4_TIGER_COUNT):
            if do_tiger_stops:
                config.tiger_block[i].enable = 1 
                # TiGer starts will be config'd to use positive pulses
                config.dc_offset[i] = self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_18
                config.tiger_block[i].start = i * 100 # delay each channel's start
                config.tiger_block[i].stop = config.tiger_block[i].start + pulse_width
                config.tiger_block[i].negate = 0
                config.tiger_block[i].retrigger = 0
                config.tiger_block[i].extend = 0
                config.tiger_block[i].enable_lemo_output = 1
                config.tiger_block[i].sources = self.TIMETAGGER4_TRIGGER_SOURCE_AUTO
            else:
                config.tiger_block[i].enable = 0
                config.dc_offset[i] = read_channel_dc_offset
    
        # check that it was configured by calling get_configure
        self.configure()
        
        # Prepare the read_in and read_out objects for reading.
        # By default, make acknowledge_last_read True
        self.get_read_config(acknowledge_last_read_bool = True)
        # self.get_read_config(acknowledge_last_read_bool = False)
        self.get_read_data()
           

    # def load_tt4_ext_trig(self,
    #                       read_window_ns = 1000
    #               ):
    #     '''
    #     Function to load the timetagger4 for basic counting applications. Use
    #     this function to configure the channels to read from and the timing generator.
        
    #     Params:
    #         read_channels: list(int) = []
    #             List of ints of the channels to read from. Channel A -> 0, etc.
    #         read_channel_dc_offset: float = 1.0
    #             Dc offset voltage value for the read channels. 
    #         ext_trig_dc_offset: float = 1.0
    #             Dc offset voltage value input to expect from ext triggers
    #         do_tiger_start: bool = False
    #             if True, TiGer pulses will be used to start capture, at a frequency
    #             of ref_trig_freq_Hz. A physical output pulse with width ref_trig_pulse_width_ns
    #             will be generated
    #         do_tiger_stops: bool = False
    #             if True, TiGer pulses will be used to stop capture. 
    #             NOT IMPLIMENTED
    #         do_continuous: bool = False
    #             if True, continuous capture will be used
    #         read_window_ns: int = 50000
    #             Duration of the read window
    #         ref_trig_freq_Hz: int = 20000
    #             Frequency used for TiGer start pulse generation
    #         ref_trig_pulse_width_ns: int = 10
    #             Pulse width used for TiGer start pulse generation
    #     '''
    #     # make sure we have static info on the TT4Manager instance
    #     try:
    #         static = self.static
    #     except Exception:
    #         self.get_static_info()
    #         static = self.static
            
    #     # make sure we have config info on the TT4Manager instance
    #     try:
    #         config = self.config
    #     except Exception:
    #         self.get_default_configuration()
    #         config = self.config
            
    #     # Ext trigger on channel S
    #     config.tdc_mode = self.TIMETAGGER4_TDC_MODE_GROUPED
    #     config.tiger_block[0].enable =  0
    #     config.dc_offset[0] =  self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_25
    #     config.trigger[self.TIMETAGGER4_TRIGGER_S].rising = True
    #     config.trigger[self.TIMETAGGER4_TRIGGER_S].falling = False
        
    #     # Bin size, in ps, that the TT4 is quantized in.
    #     # This is in the param_info, but we need it before we call that info...
    #     binsize = 800 #ps
        
    #     # Adjust the readout_window to # of bins based on binsize (ps)
    #     read_window_bins = int(read_window_ns * (1000 / binsize))
    #     # print(read_window_bins)
    #     # Read on channel A
    #     config.channel[self.TIMETAGGER4_TRIGGER_A].enabled = True
    #     config.tiger_block[1].enable =  0
    #     config.dc_offset[1] =  self.TIMETAGGER4_DC_OFFSET_P_LVCMOS_25
    #     config.trigger[self.TIMETAGGER4_TRIGGER_A].rising = True
    #     config.trigger[self.TIMETAGGER4_TRIGGER_A].falling = False
    #     config.channel[self.TIMETAGGER4_TRIGGER_A].start = 0
    #     config.channel[self.TIMETAGGER4_TRIGGER_A].stop = ctypes.c_uint32(read_window_bins)
        
        
    #     # check that it was configured by calling get_configure
    #     self.configure()
        
    #     # Prepare the read_in and read_out objects for reading.
    #     # By default, make acknowledge_last_read True
    #     self.get_read_config(acknowledge_last_read_bool = True)
    #     self.get_read_data()
        
        
    def read_packet_counts(self):
        '''
        Once the tt4 has been initialized, loaded, and started, call this function
        to read the packets.
        
        NOTE: This function currently only reads the first packet... I can't get 
        at the other packets because one function: crono_next_packet from the dll
        is not available.
        
        Use next functon, read_counts_internal() to read all packets available
        
        Params:
            # new_samples: list = []
            #     A list to add the number of counts to. Currently, only one hit_count
            #     is returned in a list of size 1.
        Returns:
            hit_count
            # new_samples: list
            #     List populated with the hit_counts
            
        '''
        # no way to iterate through all the packets... this will just read 
        # the first packet of the read data
        packet_p = self.read_data.first_packet # this is a pointer to the packet
        # print(packet_p)
        # packet_last_p = self.read_data.last_packet # this is a pointer to the packet
        # print(packet_last_p)
        
        # Once i can iterate through the packets, I can make sure we only
        # read the packets in the read data
        # pf_void = ctypes.cast(pf, ctypes.c_void_p).value
        # pl_void = ctypes.cast(read_data.last_packet, ctypes.c_void_p).value
        # # while pf_void <= pl_void:
        # print("first packet: {}".format(pf_void))
        # print("last packet: {}".format(pl_void))
        # print("Difference {}".format(pl_void - pf_void))
        # print("")
                
        packet = packet_p.contents
                
        # # if packet_count % update_count == 0:
            
        hit_count = 2 * packet.length
        if packet.flags & 1 != 0:
            hit_count -= 1
            
        # self.acknowledge(packet_p)
        # new_samples.append(hit_count)
        
        return hit_count
            
    def read_counts_internal(self, num_to_read):
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
        num_to_read_int = int(num_to_read)
        return_counts = []
        return_lengths = (ctypes.c_int * num_to_read_int)()
        return_flags = (ctypes.c_int * num_to_read_int)()
        self.dll_python_functions.read_counts_internal(self.device_p,
                                              ctypes.pointer(return_lengths),
                                              ctypes.pointer(return_flags),
                                              num_to_read_int)
        for i in range(num_to_read):
            count_i = return_lengths[i] * 2
            if return_flags[i] == 1:
                count_i -= 1
            return_counts.append(count_i)
        
        return return_counts
    
        
    def get_raw_timetags(self, num_to_read, max_hits_in_pckt = 8000):
        '''
        max_hits_in_pckt must be less than 8000, which is the hardware
        limit for the timetagger board. But it will make processing tags
        very slow. It is better to use less than 1000.
        '''
        # start = time.time()
        if max_hits_in_pckt > 8000:
            raise Exception("Cannot handle more than 8000 tags per read. Please lower the set max_hits_in_pckt")
        tag_buffer_size = max_hits_in_pckt * (int(num_to_read) + 1)
        raw_timetags = (ctypes.c_double * tag_buffer_size)()
        
        self.dll_python_functions.return_hit_data(self.device_p,
                                              ctypes.pointer(raw_timetags),
                                              int(num_to_read),
                                              int(max_hits_in_pckt)) 
        # end = time.time()     
        
        # print('get_raw_timetags {} s'.format(end - start))
        # print(list(raw_timetags)[:30])
        return list(raw_timetags)
    
    
    def read_timetags(self, num_to_read, max_hits_in_pckt = 8000):
        
            
        raw_timetags = self.get_raw_timetags(num_to_read, max_hits_in_pckt)
        # First check if there are any tags, if not return empty list
        # start = time.time()
        final_timetags = delete_buffer(raw_timetags)
        # end = time.time()
        # print('getting rid of buffer {} s'.format(end - start))
        
        # start = time.time()
        if num_to_read == 1: # special case if num_to_read is 1 
            timetag_array = [final_timetags]
        else:
            timetag_array = []    
            chunk = []
            for tag in final_timetags:
                if tag >= 0:
                    chunk.append(tag)
                else:
                    timetag_array.append(chunk)
                    chunk = []
                    continue
        # end = time.time()
        # print('sort tags {} s'.format(end - start))
        return timetag_array
        
        
    def read_counts(self, num_to_read, max_hits_in_pckt = 8000):
        '''
        Process and read the counts from the raw timetags
        Parameters
        ----------
        num_to_read : int
            number of individual readout windows to read

        Returns
        -------
        None.

        '''
        timetag_array = self.read_timetags(num_to_read, max_hits_in_pckt)
        
        counts = [len(x) for x in timetag_array]
        # print(counts)
        end_zeros = int(num_to_read) - len(counts)
        if end_zeros > 0:
            counts = counts + [0]*end_zeros
        return counts

def halve_list(alist):
    '''
    Generator function that will take a list and continue to halve it,
    it will return the first half (new_list) and second half (ret_list)
    '''
    new_list = alist
    while True:
        half_len_list = int(len(new_list)/2)
        ret_list = new_list[half_len_list:]
        new_list = new_list[:half_len_list]
        yield new_list, ret_list
        
def delete_buffer(raw_timetags):
    '''
    This function takes the raw timetag list, which has a large
    amount of buffer if the signal is low, and quickly removes the 
    buffer and returns a list of just the timetag values (and seperator
    values)
    
    It will delete any ending seperator values (-1's), however, in counting
    the number of tags in the function read_counts(), packets of 0 counts
    will be added to the end if the total number of sampels was not met
    '''
    
    
    # First we check that there are tags in the reading. If there aren't, 
    # return an empty list
    tags_sum_tot = sum(raw_timetags)
    buffer_len_tot = len(raw_timetags)*-1
    
    if tags_sum_tot == buffer_len_tot:
        final_timetags = []
        
    else:
        # Define the gnerator to halve the list
        gen = halve_list(raw_timetags)
        
        # For the number of times possible, halve the list and check that
        # the latter half is full of -1 buffer. If so, then remove and 
        # reiterate with first half
        # Break out once the list is more than half timetags
        for i in range(math.floor(math.log(len(raw_timetags),2))):
            buffer_half_beg, buffer_half_end = next(gen)
            tags_sum_half = sum(buffer_half_end)
            buffer_len_half = len(buffer_half_end)*-1
            if tags_sum_half != buffer_len_half:
                break
            
        # Work with the final timetag list, and starting at the end, 
        # remove buffer values
        final_timetags = buffer_half_beg + buffer_half_end
        for i, el in reversed(list(enumerate(final_timetags))):
            if el < 0:
                final_timetags.pop(i)
            else:
                break
        gen.close()
    return final_timetags
        
# %%    
if __name__ == "__main__":
    
    # Call in tt4 manager with original DLL
    
    tt4_manager = TT4Manager()
    tt4_manager.initialize_tt4()
    tt4_manager.load_tt4(
                      read_channels = [0],
                      read_channel_dc_offset = tt4_manager.TIMETAGGER4_DC_OFFSET_P_TTL,
                      ext_trig_dc_offset = tt4_manager.TIMETAGGER4_DC_OFFSET_P_LVCMOS_18,
                      delay = 0,
                      do_tiger_start = True, 
                      do_tiger_stops = False,  
                      do_continuous = False,
                      read_window_ns = 1000,
                      ref_trig_freq_Hz = 1/(1000*1e-9),
                      )
        
        
    tt4_manager.start_capture()
    tt4_manager.start_tiger()
    
    
    counts = tt4_manager.read_counts(1e2, 100)
    # timestamps = tt4_manager.read_counts_internal(1)
    
    tt4_manager.stop_tiger()
    tt4_manager.stop_capture()
    print(counts)
    #param_info = tt4_manager.para
    #print(param_info.binsize)
    
    tt4_manager.close_device()
    
    
    # raw_timetags = [100, 100, -1, 100] + [-1]*int(1e4*8000)
    # # raw_timetags = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
    
    # # First check if there are any tags
    
    # tags_sum_tot = sum(raw_timetags)
    # buffer_len_tot =  len(raw_timetags)*-1
    
    
    # tags_sum_tot = sum(raw_timetags)
    # buffer_len_tot = len(raw_timetags)*-1
    
    # if tags_sum_tot == buffer_len_tot:
    #     final_timetags = []
    # else:
    #     gen = halve_list(raw_timetags)
        
    #     for i in range(math.floor(math.log(len(raw_timetags),2))):
    #         buffer_half_beg, buffer_half_end = next(gen)
    #         tags_sum_half = sum(buffer_half_end)
    #         buffer_len_half = len(buffer_half_end)*-1
    #         if tags_sum_half != buffer_len_half:
    #             break
                
    #     final_timetags = buffer_half_beg + buffer_half_end
    #     for i, el in reversed(list(enumerate(final_timetags))):
    #         if el < 0:
    #             final_timetags.pop(i)
    #         else:
    #             break
    # gen.close()
    # print(final_timetags)
        