import re
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
    
import json
with open('settings.json') as f: 
    json_data = json.load(f) 
analog_chan = json_data['analog_channels'] #indicate which channels are in use
# for i in range(0, len(analog_chan)):
#     str = json_data[f'channel_{analog_chan[i]}']['formula']
#     print(f'{json_data[f"channel_{analog_chan[i]}"]["name"]}(channel_{analog_chan[i]})')
#     print(str)
#     m, b = process_equation(str)
#     print(f'm: {m}, b: {b}')
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

print(analog_chan, Fs_name, m, b, units)
