"""Example for writing digital signal."""
import nidaqmx
from nidaqmx.constants import LineGrouping
from datetime import datetime as dt
from datetime import timedelta as td
# valve1_timer_on = 2 #minutes
# valve1_timer_off = 3 #minutes
# valve2_timer_on = 1 #minutes
# valve2_timer_off = 5 #minutes
# valve1_state = False
# valve2_state = True
def valve_state_conversion(valve1, valve2, valve3, valve4):
        binary_array = [valve1, 0, valve2, 0, valve3, 0, valve4, 0]
        decimal_value = 0
        for i in range(len(binary_array)):
            bit = binary_array[i]
            decimal_value += bit * (2 ** i)

        return decimal_value

# def valve_thread():
#     global valve1_timer_off, valve2_timer_off, valve2_timer_on, valve1_timer_on, valve1_state, valve2_state
#     valve1_timer = dt.now()
#     valve2_timer = dt.now()
#     valve1_interval = valve1_timer_on if valve1_state else valve1_timer_off
#     valve2_interval = valve2_timer_on if valve2_state else valve2_timer_off
#     changed_state = True
#     print(dt.now(),' Starting')
#     while True:
#         if dt.now() - valve1_timer >= td(minutes=valve1_interval):
#             valve1_state = not valve1_state
#             valve1_interval = valve1_timer_on if valve1_state else valve1_timer_off
#             valve1_timer = dt.now()
#             changed_state = True
#             print(dt.now(),' Switching valve1')
#         if dt.now() - valve2_timer >= td(minutes=valve2_interval):
#             valve2_state = not valve2_state
#             valve2_interval = valve2_timer_on if valve2_state else valve2_timer_off
#             valve2_timer = dt.now()
#             changed_state = True
#             print(dt.now(),'Switching valve2')
#         if changed_state:
#             changed_state = False
#             with nidaqmx.Task() as task:
#                 task.do_channels.add_do_chan(
#                     "Dev1/port1/line0:3", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
#                 )
#                 task.write(valve_state_conversion(valve1_state, valve2_state))
# valve_thread()
with nidaqmx.Task() as task:
    task.do_channels.add_do_chan(
        "Dev1/port1/line0:7", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
    )

    # try:
    #     print("N Lines 1 Sample Boolean Write (Error Expected): ")
    #     print(task.write([True, False, True, False]))
    # except nidaqmx.DaqError as e:
    #     print(e)

    #print("1 Channel N Lines 1 Sample Unsigned Integer Write: ")
    print(task.write(valve_state_conversion(False, True, False, False), auto_start=True)) #0000 ,0001(Valve1 on), 0010, 0011(Valve1), 0100(Valve2), 0101(Both), 0110(Valve2)

    # print("1 Channel N Lines N Samples Unsigned Integer Write: ")
    # print(task.write([1, 2, 4, 8], auto_start=True))

    
    