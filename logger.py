'''
Authors: Yoel Ghebrecristos and Alvin La
Institution: University of California Irvine
Department: Earth Science
'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration, LineGrouping
from collections import deque
import time
import os
from datetime import datetime as dt
from datetime import timedelta as td
import csv
import threading


'''
****************** INSTRUCTIONS ******************

csv_create_file_timer - How often a new CSV file is created
csv_datalog_freq - how often the datas are logged into csv file (default 2points every second )
history_length - how much information is displayed over a certain amount of time (900s = 15 min)
num_of_channels - how many analog channels we are using on the device
samples_per_channel - number of samples device returns every interval

valve1_timer_on - ontrolls the time on for valve 1
valve1_timer_off - controlls the time off for valve 1 
valve2_timer_on - controlls the time on for valve 2 
valve2_timer_off - controlls the time off for valve 2 
valve1_state - initial valve 1 state
valve2_state - initial valve 2 state

****************************************************
'''



'''
****************** INSTRUCTIONS ******************

csv_create_file_timer - How often a new CSV file is created
csv_datalog_freq - how often the datas are logged into csv file (default 2points every second )
history_length - how much information is displayed over a certain amount of time (900s = 15 min)
num_of_channels - how many analog channels we are using on the device
samples_per_channel - number of samples device returns every interval

valve1_timer_on - ontrolls the time on for valve 1
valve1_timer_off - controlls the time off for valve 1 
valve2_timer_on - controlls the time on for valve 2 
valve2_timer_off - controlls the time off for valve 2 
valve1_state - initial valve 1 state
valve2_state - initial valve 2 state

****************************************************
'''

csv_create_file_timer = 1  # hours
csv_datalog_freq = 0.47 # seconds
history_length = 900  # seconds
samples_per_channel = 50

#num_of_channels = 5 #indicate number of channels
analog_chan = [0, 1, 2, 3, 4, 5, 6, 7] #indicate which channels are in use

#num_of_valves = 3  # indicate num of valves in use
valve_in_use = [1, 3]

#### VALVE 1 ####### (Pneumatic valve)
valve1_state = False  # initial valve state
valve1_timer_on = 5  # minutes
valve1_timer_off = 55  # minutes

#### VALVE 2 ####### (Diversion/Suckback/SO2)
valve2_state = False  # initial valve state
valve2_timer_on = 0.5  # minutes
valve2_timer_off = 4.5  # minutes

#### VALVE 3 #######
valve3_state = False  # initial valve state
valve3_timer_on = 1  # minutes
valve3_timer_off = 9  # minutes

#### VALVE 4 #######
valve4_state = False  # initial valve state
valve4_timer_on = 1  # minutes
valve4_timer_off = 5  # minutes

proccessed_Fs = ['F1 = N2','F2 = SF6','F3 = SO2','F4 = EVAC','F5 = TOR', 'F6 = ', 'F7 = ' , 'F8 = ']

def proccess_channel(data):
    process_1 = [1.0646 * x + 0.0013 for x in data[0]] # N_2
    process_2 = [21.468 * x - 0.3443 for x in data[1]] # SF_6
    process_3 = [x for x in data[3]]
    process_4 = [x for x in data[6]]
    process_5 = [6.8967 * x + 0.185 for x in data[4]] # EVAC
    process_6 = [10.468 * x + 0.8423 for x in data[5]] # SO_2
    process_7 = [x for x in data[6]]
    process_8 = [20.00 * x for x in data[7]] # TOR
    return [process_1, process_2, process_3, process_4, process_5, process_6, process_7, process_8]

def valve_state_conversion(valve1, valve2, valve3, valve4):
        binary_array = [valve1, 0, valve2, 0, valve3, 0, valve4, 0]
        #print(binary_array)
        decimal_value = 0
        for i in range(len(binary_array)):
            bit = binary_array[i]
            decimal_value += bit * (2 ** i)
        #print(decimal_value)
        return decimal_value

def create_csv_file(file_name):
    with open(file_name, 'w', newline='') as csv_file:
        # Your CSV writing code here, for example:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Date/Time'] +  [f'Channel_{i}' for i in range(0, len(analog_chan))] + proccessed_Fs)

    print(f"CSV file '{file_name}' created.")



def log_data(f_name, data):
    with open(f_name, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(data)
folder_path = "csv_folder"
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

current_time = dt.now()
second_timer = dt.now()
time_str = current_time.strftime("%Y_%m_%d_%H_%M_%S")
current_data = [time_str, 0]
file_name = f"{folder_path}/data_{time_str}.csv"
create_csv_file(file_name)

# Configure NI DAQmx settings
task = nidaqmx.Task()
for i in range(0, len(analog_chan)):
    task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{analog_chan[i]}", terminal_config=TerminalConfiguration.RSE)
task.timing.cfg_samp_clk_timing(rate=100, sample_mode=AcquisitionType.CONTINUOUS)
# Initialize variables for data storage and plotting
num_samples = int(task.timing.samp_clk_rate * history_length)
time_values = np.linspace(-history_length, 0, num_samples)
data_buffer = deque(maxlen=num_samples)
time_buffer = deque(maxlen=num_samples)
plt_channel = 0

def clear_buffer():
    global data_buffer, time_buffer
    data_buffer = deque(maxlen=num_samples)
    time_buffer = deque(maxlen=num_samples)
    
def next_button(command):
    clear_buffer()
    global plt_channel, ax
    if plt_channel != len(analog_chan) - 1:
        plt_channel = plt_channel + 1
    else:
        plt_channel = 0
    ax.set_title(f'F{plt_channel + 1}')
    ax.set_ylabel(f'{proccessed_Fs[plt_channel]}')
    

def prev_button(command):
    global plt_channel, ax
    clear_buffer()
    if not plt_channel:
        plt_channel = len(analog_chan) - 1
    else:
        plt_channel = plt_channel - 1
    ax.set_title(f'F{plt_channel + 1}')
    ax.set_ylabel(f'{proccessed_Fs[plt_channel]}')

# Create the plot
plt.ion()  # Enable interactive mode for dynamic updating
fig, ax = plt.subplots()
line, = ax.plot(time_values, np.zeros(num_samples))
ax.set_xlabel('Time (s)')
ax.set_ylabel(f'{proccessed_Fs[plt_channel]}')
ax.set_title(f'F{plt_channel + 1}')
task.start()
nxt_button_ax = plt.axes([0.85, 0.9, 0.1, 0.04])  # [left, bottom, width, height]
nxt_button = Button(nxt_button_ax, 'Next')
nxt_button.on_clicked(next_button)

prv_button_ax = plt.axes([0.7, 0.9, 0.1, 0.04])  # [left, bottom, width, height]
prv_button = Button(prv_button_ax, 'Previous')
prv_button.on_clicked(prev_button)
# valve1_timer = dt.now()
# valve2_timer = dt.now()
valve_start_timer = [dt.now(), dt.now(), dt.now()]
valve_duration = [valve1_timer_on if valve1_state else valve1_timer_off, 
                  valve2_timer_on if valve2_state else valve2_timer_off,
                  valve3_timer_on if valve3_state else valve3_timer_off,
                  valve4_timer_on if valve4_state else valve4_timer_off]
valve_states = [valve1_state if len(valve_in_use) > 0 else False, 
                valve2_state if len(valve_in_use) > 1 else False, 
                valve3_state if len(valve_in_use) > 2 else False, 
                valve4_state if len(valve_in_use) > 3 else False]
valve_timer_on = [valve1_timer_on, valve2_timer_on, valve3_timer_on, valve4_timer_on]
valve_timer_off = [valve1_timer_off, valve2_timer_off, valve2_timer_off, valve3_timer_off]
changed_state = True
print(dt.now(), "Starting time")
while True:
    try:
        new_data = task.read(number_of_samples_per_channel=samples_per_channel)  # Read 50 samples
        values = [new_data[i][-1] for i in range(0, len(analog_chan))]
        processed_data = proccess_channel(new_data)
        processed_values = [processed_data[i][-1] for i in range(0, len(analog_chan))]
        #print(processed_data)
        timestamp = time.time()
        data_buffer.extend(processed_data[plt_channel])
        time_buffer.extend([timestamp] * len(processed_data[plt_channel]))

        time_diff = np.array(time_buffer) - time_buffer[-1]
        mask = time_diff > -history_length
        line.set_xdata(-time_diff[mask])
        line.set_ydata(np.array(data_buffer)[mask])
        now = dt.now()
        current_data = [dt.now().strftime("%Y-%m-%d %H:%M:%S")] + values + processed_values
        ax.relim()
        ax.autoscale_view()
        plt.pause(0.01)  # Pause to allow the plot to update
        if dt.now() - second_timer >= td(seconds=csv_datalog_freq):
            log_data(file_name, current_data)
            second_timer = dt.now()
        if dt.now() - current_time >= td(hours=csv_create_file_timer):
            current_time = dt.now()
            time_str = current_time.strftime("%Y_%m_%d_%H_%M_%S")
            file_name = f"{folder_path}/data_{time_str}.csv"
            create_csv_file(file_name)
        for i in range(0, len(valve_in_use)):
            if dt.now() - valve_start_timer[valve_in_use[i] - 1] >= td(minutes=valve_duration[i]):
                valve_states[valve_in_use[i] - 1] = not valve_states[i]
                valve_duration[valve_in_use[i] - 1] = valve_timer_on[valve_in_use[i] - 1] if valve_states[valve_in_use[i] - 1] else valve_timer_off[valve_in_use[i] - 1]
                valve_start_timer[valve_in_use[i] - 1] = dt.now()
                changed_state = True
                print(dt.now(), f'Switching Valve{valve_in_use[i]}')
        if changed_state:
            changed_state = False
            task.stop()
            task.close()
            task = nidaqmx.Task()
            task.do_channels.add_do_chan(
                    "Dev1/port1/line0:7", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
            task.start()
            task.write(valve_state_conversion(valve_states[0], 
                                              valve_states[1], 
                                              valve_states[2], 
                                              valve_states[3]), auto_start=True)
            task.stop()
            task.close()
            task = nidaqmx.Task()

            for i in range(0, len(analog_chan)):
                task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{analog_chan[i]}", terminal_config=TerminalConfiguration.RSE)
            task.timing.cfg_samp_clk_timing(rate=100, sample_mode=AcquisitionType.CONTINUOUS)
        
    except (KeyboardInterrupt,SystemExit):
        task.stop()
        task.close()
        plt.ioff()  # Turn off interactive mode
        break