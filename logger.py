"""
Example: DAQmx-Python Analog Input Acquisition and Plot With History (NI 2023)
Author: Davit Danielyan

DISCLAIMER: The attached Code is provided As Is. It has not been tested or validated as a product, for use in a
deployed application or system, or for use in hazardous environments. You assume all risks for use of the Code and
use of the Code is subject to the Sample Code License Terms which can be found at: http://ni.com/samplecodelicense
"""

import numpy as np
import matplotlib.pyplot as plt
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
csv_datalog_freq = 0.97 #seconds
history_length = 900  # seconds
samples_per_channel = 50
num_of_channels = 5

def create_csv_file(file_name):
    with open(file_name, 'w', newline='') as csv_file:
        # Your CSV writing code here, for example:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Date/Time', 'Value'])

    print(f"CSV file '{file_name}' created.")
    

# def log_data(f_name):
#     global current_data
#     with open(f_name, 'a', newline='') as csv_file:
#         csv_writer = csv.writer(csv_file)
#         while True:
#             csv_writer.writerow(current_data)
#             time.sleep(1)

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

# Create the plot
plt.ion()  # Enable interactive mode for dynamic updating
fig, ax = plt.subplots()
line, = ax.plot(time_values, np.zeros(num_samples))
ax.set_xlabel('Time (s)')
ax.set_ylabel('Voltage (V)')
ax.set_title('Analog Input from Dev1/ai0')
task.start()

while True:
    try:
        new_data = task.read(number_of_samples_per_channel=samples_per_channel)  # Read 50 samples
        timestamp = time.time()
        data_buffer.extend(new_data)
        time_buffer.extend([timestamp] * len(new_data))

        time_diff = np.array(time_buffer) - time_buffer[-1]
        mask = time_diff > -history_length
        line.set_xdata(-time_diff[mask])
        line.set_ydata(np.array(data_buffer)[mask])
        value1 = data_buffer[-1]
        print(value1)
        now = dt.now()
        current_data = [dt.now().strftime("%Y-%m-%d %H:%M:%S"), value1]
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