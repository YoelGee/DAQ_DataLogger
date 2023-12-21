from datetime import datetime as dt
from datetime import timedelta as td
import json
with open('settings.json') as f: 
    json_data = json.load(f) 
valve_in_use = json_data['valves_in_use']
valve_start_timer = [dt.now(), dt.now(), dt.now(), dt.now()]
valve_timing = [json_data[f'valve{i + 1}']['timing'] if len(json_data[f'valve{i + 1}']['timing']) > 0 else [0, False] for i in range(0, 4)]
print(valve_timing)
valve_counters = [0,0,0,0]
print("Starting time: ", dt.now())
while(True):
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
            