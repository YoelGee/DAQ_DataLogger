import os
import pandas as pd
sub_directory = 'csv_folder'
output_directory = 'csv_folder_new'
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
files = os.listdir(sub_directory)
for file in files:
    file_path = os.path.join(sub_directory, file)
    df = pd.read_csv(file_path, header=0)
    headers = df.columns.values
    df = df.values.tolist()
    index = 1
    for i in range(1, len(df)):
        if df[i][0] != df[i-1][0]:
            df[index] = df[i]
            index += 1
    output_file_path =  os.path.join(output_directory, file)
    output_df = pd.DataFrame(df[:index], columns=headers)
    output_df.to_csv(output_file_path, index=False)
