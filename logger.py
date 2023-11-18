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
import time

# Configure NI DAQmx settings
task = nidaqmx.Task()
task.ai_channels.add_ai_voltage_chan("Dev1/ai0", terminal_config=TerminalConfiguration.RSE)
task.timing.cfg_samp_clk_timing(rate=1000, sample_mode=AcquisitionType.CONTINUOUS)

# Initialize variables for data storage and plotting
history_length = 5  # seconds
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
        new_data = task.read(number_of_samples_per_channel=50)  # Read 50 samples
        timestamp = time.time()

        data_buffer.extend(new_data)
        time_buffer.extend([timestamp] * len(new_data))

        time_diff = np.array(time_buffer) - time_buffer[-1]
        mask = time_diff > -history_length
        line.set_xdata(-time_diff[mask])
        line.set_ydata(np.array(data_buffer)[mask])
        ax.relim()
        ax.autoscale_view()
        plt.pause(0.01)  # Pause to allow the plot to update
    except (KeyboardInterrupt,SystemExit):
        task.stop()
        task.close()
        plt.ioff()  # Turn off interactive mode
        break