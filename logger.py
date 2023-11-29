'''
Authors: Yoel Ghebrecristos and Alvin La
Institution: University of California Irvine
Department: Earth Science
'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
from collections import deque
import pandas as pd
import time
import os
from datetime import datetime as dt
from datetime import timedelta as td
import csv

csv_create_file_timer = 1  # hours
csv_datalog_freq = 0.47 # seconds
history_length = 900  # seconds
num_of_channels = 5
samples_per_channel = 25

def proccess_channel(data):
    process_1 = 1.0646 * data[0] + 0.0013
    process_2 = 10.468 * data[1] + 0.8423
    process_3 = 6.8967 * data[2] + 0.185
    process_4 = 21.468 * data[3] - 0.3443
    process_5 = 20.00 * data[4]
    
    return process_1, process_2, process_3, process_4, process_5


def create_csv_file(file_name):
    with open(file_name, 'w', newline='') as csv_file:
        # Your CSV writing code here, for example:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Date/Time'] +  [f'Channel_{i}' for i in range(0, num_of_channels)])

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
for i in range(0, num_of_channels):
    task.ai_channels.add_ai_voltage_chan(f"Dev1/ai{i}", terminal_config=TerminalConfiguration.RSE)
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
    if plt_channel != num_of_channels - 1:
        plt_channel = plt_channel + 1
    else:
        plt_channel = 0
    ax.set_title(f'F{plt_channel + 1}')

def prev_button(command):
    global plt_channel, ax
    clear_buffer()
    if not plt_channel:
        plt_channel = num_of_channels - 1
    else:
        plt_channel = plt_channel - 1
    ax.set_title(f'F{plt_channel + 1}')
# Create the plot
plt.ion()  # Enable interactive mode for dynamic updating
fig, ax = plt.subplots()
line, = ax.plot(time_values, np.zeros(num_samples))
ax.set_xlabel('Time (s)')
ax.set_ylabel('Voltage (V)')
ax.set_title(f'F{plt_channel + 1}')
task.start()

nxt_button_ax = plt.axes([0.85, 0.9, 0.1, 0.04])  # [left, bottom, width, height]
nxt_button = Button(nxt_button_ax, 'Next')
nxt_button.on_clicked(next_button)

prv_button_ax = plt.axes([0.7, 0.9, 0.1, 0.04])  # [left, bottom, width, height]
prv_button = Button(prv_button_ax, 'Previous')
prv_button.on_clicked(prev_button)


while True:
    try:
        new_data = task.read(number_of_samples_per_channel=samples_per_channel)  # Read 50 samples
        values = [new_data[i][-1] for i in range(0, num_of_channels)]
        proccessed_values = proccess_channel(values)
        timestamp = time.time()
        data_buffer.extend(proccessed_values[plt_channel])
        time_buffer.extend([timestamp] * len(proccessed_values[plt_channel]))

        time_diff = np.array(time_buffer) - time_buffer[-1]
        mask = time_diff > -history_length
        line.set_xdata(-time_diff[mask])
        line.set_ydata(np.array(data_buffer)[mask])
        now = dt.now()
        current_data = [dt.now().strftime("%Y-%m-%d %H:%M:%S")] + values + proccessed_values
        ax.relim()
        ax.autoscale_view()
        plt.pause(0.01)  # Pause to allow the plot to update
        if dt.now() - second_timer >= td(seconds=csv_datalog_freq):
            log_data(file_name, current_data)
            second_timer = dt.now()
        if dt.now() - current_time >= td(hours=csv_create_file_timer):
            current_time = dt.now()
            time_str = current_time.strftime("%Y%m%d_%H%M%S")
            file_name = f"{folder_path}/data_{time_str}.csv"
            create_csv_file(file_name)
        
        
        
    except (KeyboardInterrupt,SystemExit):
        task.stop()
        task.close()
        plt.ioff()  # Turn off interactive mode
        break