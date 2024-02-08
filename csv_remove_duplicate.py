import os
import pandas as pd
sub_directory = 'csv_files'


# List all files in the directory
files = os.listdir(sub_directory)
for file in files:
    file_path = os.path.join(sub_directory, file)
    df = pd.read_csv(file_path, header=0)
    df = df.values.tolist()
    headers = df[0]
    df = df[1:]
    index = 1
    for i in range(1, len(df)):
        if df[i][0] != df[i-1][0]:
            df[index] = df[i]
            index += 1
    output_df = pd.DataFrame(df, columns=headers)
    output_df.to_csv(file_path, index=False)
