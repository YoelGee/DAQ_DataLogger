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

import json
with open('settings.json') as f: 
    json_data = json.load(f) 

csv_create_file_timer = 1  # hours
csv_datalog_freq = 0.47 # seconds
history_length = 900  # seconds
samples_per_channel = 50

#num_of_channels = 5 #indicate number of channels
analog_chan = json_data['analog_channels'] #indicate which channels are in use

#num_of_valves = 3  # indicate num of valves in use
valve_in_use = json_data['valves_in_use']

#### VALVE 1 ####### (Pneumatic valve)
valve1_state = json_data['valve1']['initial_state']  # initial valve state
valve1_timer_on = json_data['valve1']['time_on']   # minutes
valve1_timer_off = json_data['valve1']['time_off']   # minutes

#### VALVE 2 ####### (Diversion/Suckback/SO2)
valve2_state = json_data['valve2']['initial_state']  # initial valve state
valve2_timer_on = json_data['valve2']['time_on']   # minutes
valve2_timer_off = json_data['valve2']['time_off']   # minutes

#### VALVE 3 #######
valve3_state = json_data['valve3']['initial_state']  # initial valve state
valve3_timer_on = json_data['valve3']['time_on']   # minutes
valve3_timer_off = json_data['valve3']['time_off']   # minutes

#### VALVE 4 #######
valve4_state = json_data['valve4']['initial_state']  # initial valve state
valve4_timer_on = json_data['valve4']['time_on']   # minutes
valve4_timer_off = json_data['valve4']['time_off']   # minutes
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
standard_unit = json_data['standard_unit']
for i in range(0, len(analog_chan)):
    str = json_data[f'channel_{analog_chan[i]}']['formula']
    #print(f'channel_{analog_chan[i]}')
    #print(str)
    m_temp, b_temp = process_equation(str)
    m.append(m_temp)
    b.append(m_temp)
    Fs_name.append(json_data[f'channel_{analog_chan[i]}']['name'])
    unit = json_data[f'channel_{analog_chan[i]}']['units']
    if unit == standard_unit or (unit != 'mL/min' and unit != 'L/min'):
        units.append([1, unit])
    elif standard_unit == 'L/min': #means channel units mL and standard is L
        units.append([0.001, standard_unit])
    else: #means channel units L and standard is mL
        units.append([1000, standard_unit])
#proccessed_Fs = ['F1 = N2','F2 = SF6','F3 = SO2','F4 = EVAC','F5 = TOR', 'F6 = ', 'F7 = ' , 'F8 = ']
print(analog_chan, Fs_name, m, b, units)
def proccess_channel(data):
    process = []
    for i in range(0, len(analog_chan)):
        process.append([(m[i] * x + b[i])* units[i][0] for x in data[i]])
    return process

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
        csv_writer.writerow(['Date/Time'] +  [f'Channel_{analog_chan[i]}' for i in range(0, len(analog_chan))] + Fs_name)

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
    ax.set_title(f'F{analog_chan[plt_channel]}(Channel {analog_chan[plt_channel]})')
    ax.set_ylabel(f'{Fs_name[plt_channel]}({units[plt_channel][1]})')
    

def prev_button(command):
    global plt_channel, ax
    clear_buffer()
    if not plt_channel:
        plt_channel = len(analog_chan) - 1
    else:
        plt_channel = plt_channel - 1
    ax.set_title(f'F{analog_chan[plt_channel]}(Channel {analog_chan[plt_channel]})')
    ax.set_ylabel(f'{Fs_name[plt_channel]}({units[plt_channel][1]})')

# Create the plot
plt.ion()  # Enable interactive mode for dynamic updating
fig, ax = plt.subplots()
line, = ax.plot(time_values, np.zeros(num_samples))
ax.set_xlabel('Time (s)')
ax.set_title(f'F{analog_chan[plt_channel]}(Channel {analog_chan[plt_channel]})')
ax.set_ylabel(f'{Fs_name[plt_channel]}({units[plt_channel][1]})')
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
        #print(new_data)
        processed_data = proccess_channel(new_data)
        #print(processed_data)
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
                task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{analog_chan[i] - 1}", terminal_config=TerminalConfiguration.RSE)
            task.timing.cfg_samp_clk_timing(rate=100, sample_mode=AcquisitionType.CONTINUOUS)
        
    except (KeyboardInterrupt,SystemExit):
        task.stop()
        task.close()
        plt.ioff()  # Turn off interactive mode
        break