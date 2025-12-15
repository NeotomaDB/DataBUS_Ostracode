import pandas as pd
import os 

def csv_splitter(data, params=['Handle'], path = 'data/splitted'):
    split_files = path
    if not os.path.exists(split_files):
                os.makedirs(split_files)

    data_groups = data.groupby(by=params)
    ngr = data_groups.ngroups
    print(f"Number of groups: {ngr}.")
    for group, rows in data_groups:
        ngr -= 1
        counter = (ngr / data_groups.ngroups) * 100
        if ngr % 10 == 0: 
            print(f"Missing: {counter:.2f}%")
        filename = f"{path}/{group}.csv"
        rows.to_csv(filename, index=False)
    print("Finished")