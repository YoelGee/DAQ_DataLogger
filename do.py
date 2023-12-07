"""Example for writing digital signal."""
import nidaqmx
from nidaqmx.constants import LineGrouping
def valve_state_conversion(valve1, valve2):
        binary_array = [0, valve2, 0, valve1]
        decimal_value = 0
        binary_array.reverse()  # Reverse the array to start from the least significant bit

        for i in range(len(binary_array)):
            bit = binary_array[i]
            decimal_value += bit * (2 ** i)

        return decimal_value

with nidaqmx.Task() as task:
    task.do_channels.add_do_chan(
        "Dev1/port1/line0:3", line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
    )

    # try:
    #     print("N Lines 1 Sample Boolean Write (Error Expected): ")
    #     print(task.write([True, False, True, False]))
    # except nidaqmx.DaqError as e:
    #     print(e)

    #print("1 Channel N Lines 1 Sample Unsigned Integer Write: ")
    print(task.write(valve_state_conversion(True, True), auto_start=True)) #0000 ,0001(Valve1 on), 0010, 0011(Valve1), 0100(Valve2), 0101(Both), 0110(Valve2)

    # print("1 Channel N Lines N Samples Unsigned Integer Write: ")
    # print(task.write([1, 2, 4, 8], auto_start=True))

    
    