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
import re
import json

with open('settings.json') as f: 
    json_data = json.load(f) 

# grabs settings from the settings.json file
csv_create_file_timer = json_data['csv_settings']['csv_create_file_time_in_hours'] 
csv_datalog_freq = 1/json_data['csv_settings']['csv_data_logging_freq'] 

history_length = json_data['graph_settings']['graph_window_time_in_seconds']  
samples_per_channel = json_data['graph_settings']['samples_per_channel']

valve_in_use = json_data['valve_settings']['valves_in_use']
valve_timing = [json_data['valve_settings'][f'valve{i + 1}']['timing'] 
                if len(json_data['valve_settings'][f'valve{i + 1}']['timing']) > 0 
                else [[0, False]] for i in range(0, 4)]


analog_chan = json_data['analog_settings']['analog_channels'] 
standard_unit = json_data['analog_settings']['standard_unit']


# this function takes the formula mx+b as a string and gets the m and b
def process_equation(equation):
    # Define a regular expression pattern to match the mx + b format
    pattern = re.compile(r'([-+]?\d*\.?\d*)\s*x\s*([-+]?\d*\.?\d*)')

    # Search for the pattern in the equation
    match = pattern.search(equation)

    if match:
        # Extract the values of m and b from the matched groups
        m = float(match.group(1)) if match.group(1) else 1.0
        b = float(match.group(2)) if match.group(2) else 0.0
        return m, b
    else:
        # If no match is found, return None for both m and b
        return None, None
m = []
b = []
Fs_name = []
units = []
#loops through settting file and gets analog channel data
for i in range(0, len(analog_chan)):
    #gets the formula of the channel
    str = json_data['analog_settings'][f'channel_{analog_chan[i]}']['formula']
    #gets the m and b of the formula and stores it into a list
    m_temp, b_temp = process_equation(str)
    m.append(m_temp)
    b.append(m_temp)
    #gets the channel name
    Fs_name.append(json_data['analog_settings'][f'channel_{analog_chan[i]}']['name'])
    #gets the unit of the formula
    unit = json_data['analog_settings'][f'channel_{analog_chan[i]}']['units']
    #checks if the units match with the standard units L/min or sccm
    if unit == standard_unit or (unit != 'mL/min' and unit != 'L/min' and unit != 'sccm'):
        units.append([1, unit])
    elif standard_unit == 'L/min': #means channel units mL and standard is L
        units.append([0.001, standard_unit])
    else: #means channel units L and standard is mL/min or sccm
        units.append([1000, standard_unit])
print(analog_chan, Fs_name, m, b, units)

#function converts voltage to flow using the equations
def proccess_channel(data):
    process = []
    for i in range(0, len(analog_chan)):
        process.append([(m[i] * x + b[i])* units[i][0] for x in data[i]])
    return process

#function is used to convert the 4 valve states into a decimal value which is used to communicate with nidaq device
def valve_state_conversion(valve1, valve2, valve3, valve4):
        binary_array = [valve1, 0, valve2, 0, valve3, 0, valve4, 0]
        #print(binary_array)
        decimal_value = 0
        for i in range(len(binary_array)):
            bit = binary_array[i]
            decimal_value += bit * (2 ** i)
        #print(decimal_value)
        return decimal_value
# creates csv file and writes out a header
def create_csv_file(file_name):
    with open(file_name, 'w', newline='') as csv_file:
        # Your CSV writing code here, for example:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Date/Time'] +  [f'Channel_{analog_chan[i]}' for i in range(0, len(analog_chan))] + Fs_name +  [f'Valve{valve_in_use[i]}_State' for i in range(0, len(valve_in_use))])

    print(f"CSV file '{file_name}' created.")

#logs data to the csv file
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
    task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{analog_chan[i] - 1}", terminal_config=TerminalConfiguration.RSE)
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
    ax.set_title(f'{Fs_name[plt_channel]}(Channel {analog_chan[plt_channel]})')
    ax.set_ylabel(f'{Fs_name[plt_channel]}({units[plt_channel][1]})')
    

def prev_button(command):
    global plt_channel, ax
    clear_buffer()
    if not plt_channel:
        plt_channel = len(analog_chan) - 1
    else:
        plt_channel = plt_channel - 1
    ax.set_title(f'{Fs_name[plt_channel]}(Channel {analog_chan[plt_channel]})')
    ax.set_ylabel(f'{Fs_name[plt_channel]}({units[plt_channel][1]})')

# Create the plot
plt.ion()  # Enable interactive mode for dynamic updating
fig, ax = plt.subplots()
line, = ax.plot(time_values, np.zeros(num_samples))
ax.set_xlabel('Time (s)')
ax.set_title(f'{Fs_name[plt_channel]}(Channel {analog_chan[plt_channel]})')
ax.set_ylabel(f'{Fs_name[plt_channel]}({units[plt_channel][1]})')
task.start()
nxt_button_ax = plt.axes([0.85, 0.9, 0.1, 0.04])  # [left, bottom, width, height]
nxt_button = Button(nxt_button_ax, 'Next')
nxt_button.on_clicked(next_button)

prv_button_ax = plt.axes([0.7, 0.9, 0.1, 0.04])  # [left, bottom, width, height]
prv_button = Button(prv_button_ax, 'Previous')
prv_button.on_clicked(prev_button)

valve_start_timer = [dt.now(), dt.now(), dt.now(), dt.now()]
valve_counters = [0,0,0,0]
changed_state = True
print(dt.now(), "Starting time")
while True:
    try:
        new_data = task.read(number_of_samples_per_channel=samples_per_channel)  # Read 50 samples
        values = [new_data[i][-1] for i in range(0, len(analog_chan))]
        processed_data = proccess_channel(new_data)
        processed_values = [processed_data[i][-1] for i in range(0, len(analog_chan))]
        timestamp = time.time()
        data_buffer.extend(processed_data[plt_channel])
        time_buffer.extend([timestamp] * len(processed_data[plt_channel]))

        time_diff = np.array(time_buffer) - time_buffer[-1]
        mask = time_diff > -history_length
        line.set_xdata(-time_diff[mask])
        line.set_ydata(np.array(data_buffer)[mask])
        now = dt.now()
        current_data = [dt.now().strftime("%Y-%m-%d %H:%M:%S")] + values + processed_values + [valve_timing[valve_in_use[i] - 1][valve_counters[valve_in_use[i] - 1]][1] for i in range(0, len(valve_in_use))]
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
            if dt.now() - valve_start_timer[valve_in_use[i] - 1] >= td(minutes=valve_timing[valve_in_use[i] - 1][valve_counters[valve_in_use[i] - 1]][0]):
                valve_start_timer[valve_in_use[i] - 1] = dt.now()
                prev_state = valve_timing[valve_in_use[i] - 1][valve_counters[valve_in_use[i] - 1]][1]
                valve_counters[valve_in_use[i] - 1] = 0 if len(valve_timing[valve_in_use[i] - 1]) - 1 == valve_counters[valve_in_use[i] - 1] else valve_counters[valve_in_use[i] - 1] + 1
                new_state = valve_timing[valve_in_use[i] - 1][valve_counters[valve_in_use[i] - 1]][1]
                #changed_state = True if new_state != prev_state else changed_state
                if(prev_state != new_state):
                    changed_state = True
                    print(dt.now(), f'Switching Valve{valve_in_use[i]} from {prev_state} to {new_state}')

        if changed_state:
            changed_state = False
            task.stop()
            task.close()
            task = nidaqmx.Task()
            task.do_channels.add_do_chan(
                    "Dev1/port1/line0:7", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
            task.start()
            task.write(valve_state_conversion(valve_timing[0][valve_counters[0]][1], 
                                              valve_timing[1][valve_counters[1]][1], 
                                              valve_timing[2][valve_counters[2]][1], 
                                              valve_timing[3][valve_counters[3]][1]), auto_start=True)
            task.stop()
            task.close()
            task = nidaqmx.Task()

            for i in range(0, len(analog_chan)):
                task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{analog_chan[i] - 1}", terminal_config=TerminalConfiguration.RSE)
            task.timing.cfg_samp_clk_timing(rate=100, sample_mode=AcquisitionType.CONTINUOUS)
        
    except (KeyboardInterrupt,SystemExit):
        task.stop()
        task.close()
        task = nidaqmx.Task()
        task.do_channels.add_do_chan(
                "Dev1/port1/line0:7", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        task.start()            
        task.write(valve_state_conversion(False, False, False, False), auto_start=True)
        task.stop()
        task.close()
        plt.ioff()  # Turn off interactive mode
        break