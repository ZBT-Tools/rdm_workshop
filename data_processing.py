import pandas as pd
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from pymongo import errors
from pymongo import MongoClient
from dotenv import load_dotenv
import chardet
import helper_functions as hf
from rich import print
import plotly.express as px
import plotly.graph_objects as go

# Retrieve complete data set processing control directives from xlsx file
processing_control_file = "./filters/Filter_BZ011.xlsx" #spezifisch fürs
processing_parameters_dict = hf.determine_processing_parameters(
    processing_control_file)
column_actions = hf.determine_column_actions(processing_control_file)

# Choose test bench
testbench_list = ['BZ011', 'BZ016', 'BZ_3Gleiche']
testbench_name = 'BZ011'

# Configure data names
set_id_key = 'Set aktuell'
set_change_key = 'change_count'
datetime_key = 'Datum'
method_key = 'Auswertemodus (c: zyklisch / lv: last value)'
window_key = 'avgN'

col_set_id, datetime_format = hf.testbench_formats(testbench_name)

# Connect to MongoDB database with credentials from separate .env file
load_dotenv()
mongodb_user = os.environ.get("MONGODB_USER")
mongodb_password = os.environ.get("MONGODB_PASS")
mongodb_ip = os.environ.get("MONGODB_IP")
if not all([mongodb_user, mongodb_password, mongodb_ip]):
    raise ValueError('Environment variables not correctly set.')
# MongoDB connection
# mongo_uri = "mongodb://"+mongodb_user+":"+mongodb_password+"@172.16.134.8
# :27017/?directConnection=true&authSource=admin"
# mongo_uri = "mongodb://localhost:27017"
# try:
#     client = MongoClient(host=mongodb_ip, port=27017, username=mongodb_user,
#                          password=mongodb_password, authSource="admin",
#                          directConnection=True)
#     # Select database and collection
#     db = client["rdm_workshop"]
#     collection = db["BZ011_Rohdaten"]
#     # Fetch all data from MongoDB collection
#     cursor = collection.find({})  # Empty filter `{}` fetches all documents
#     # Convert to DataFrame and sort by datetime column
#     df_full = pd.DataFrame(list(cursor)).sort_values([datetime_key])
# except (errors.ServerSelectionTimeoutError, errors.ConnectionFailure):
print('MongoDB server not available. Read data from test file instead.')
# File path
file_path = "./data/BZ011_Rohdaten.dat"
with open(file_path, "rb") as f:
    result = chardet.detect(f.read(100000))  # Analyze first 100KB
    detected_encoding = result["encoding"]
df_full = pd.read_csv(file_path, delimiter="\t", encoding=detected_encoding,
                 decimal=",")
df_full['Datum'] = pd.to_datetime(df_full['Datum'], format=datetime_format)


df_full = hf.count_continuous_sections(df_full, set_id_key, set_change_key)

# Add new data to time-series collection (not working correctly atm)
# df_change_count = df_full[["change_count", "_id", "Datum"]]
# hf.add_columns_to_existing_collection(
#     df_change_count, client, "rdm_workshop", "BZ011_Rohdaten", "Datum")

# Plot some control data for plausibility checks
fig_1 = px.line(df_full, x='Datum', y=['p_Luft/bar_ein', 'T_Luft_ein',
                                       'Set aktuell', 'U1', 'change_count'])
fig_1.show()

# Processing columns
process_columns = [name for name, value in column_actions.items() if value == 1]
numeric_columns = (
    df_full.select_dtypes(include=np.float64).dropna(axis=1).columns.tolist())
process_columns = list(set(process_columns) & set(numeric_columns))
# # Look only at entries with specific set number
# set_id = 13
# # Create a dataframe based on the specified set_id and the list of columns to
# # be processed and sort the dataframe by the key "Datum"
# # Fetch from database: not useful until "change_count" successfully added to
# # time-series collection in database
# # cursor = collection.find({'Set aktuell': {'$eq': set_id}})
# # df_subset = pd.DataFrame(list(cursor)).sort_values(['Datum'])[process_columns]
# df_subset = df_full[df_full['Set aktuell'] == set_id]

# Filter full data set only keeping rows with SetIDs ("Set aktuell") relevant
# for post-processing
df_filtered_rows = df_full[df_full[set_id_key].isin(
    processing_parameters_dict.keys())]

# processing_parameters = processing_parameters_dict[set_id]
processing_method_parameters = list(
    {str(i):i for i in list(processing_parameters_dict.values())}.values())
processing_method_parameters = {i: processing_method_parameters[i] for i
                                in range(len(processing_method_parameters))}
# processing_methods = set(list(processing_parameters_dict.values()))

processing_method_sets = {key: [] for key, value in
                           processing_method_parameters.items()}
for key, value in processing_parameters_dict.items():
    for index, method in processing_method_parameters.items():
        if value == method:
            processing_method_sets[index].append(key)

# Perform each of the processing methods individually on the reduced data sets
processed_data_sets = []
for key, value in processing_method_sets.items():
    df_filtered_rows_subset = (
        df_filtered_rows[df_filtered_rows[set_id_key].isin(value)])
    # test_1 = df_filtered_rows_subset.reset_index()
    # df_numeric = hf.remove_non_numeric_columns(df_filtered_rows_subset)
    grouped = df_filtered_rows_subset.groupby([set_id_key, set_change_key])

    processing_parameters = processing_method_parameters[key]
    method = processing_parameters[method_key]
    window_size = processing_parameters[window_key]
    if method == 'c':
        indexer = pd.api.indexers.FixedForwardWindowIndexer(
            window_size=window_size)
        # df_processed = grouped.rolling(indexer).mean(numeric_only=True).nth(
        #     window_size).dropna()
        df_processed = grouped[process_columns].transform(lambda x: x.rolling(
            indexer, min_periods=1).mean()).iloc[::window_size].dropna()
        new_columns = {col: col + '_averaged' for col in df_processed.columns}
        df_processed.rename(columns=new_columns, inplace=True)
    elif method == 'lv':
        df_processed = grouped[process_columns].transform(
            lambda x: x.tail(min(window_size, len(x) - 2)).mean())
        new_column_dict = {col: col + '_averaged' for col in
                           df_processed.columns}
        df_processed.rename(columns=new_column_dict, inplace=True)
        new_columns = df_processed.columns
        # Group again to only take the last value of each group
        df_processed = pd.concat(
            [df_filtered_rows_subset, df_processed], axis=1)
        df_processed = df_processed.groupby(
            [set_id_key, set_change_key]).tail(1)
        df_processed = df_processed[new_columns]
    else:
        raise ValueError('only "c" and "lv" are accepted as methods for now.')
    processed_data_sets.append(df_processed)
processed_data = pd.concat(processed_data_sets, axis=0)
data = pd.concat([df_full, processed_data], axis=1)


x_values = data[datetime_key]
columns = [set_id_key, set_change_key, 'U1', 'U1_averaged']
y_values = [data[i] for i in columns]

modes = ['lines', 'lines', 'lines', 'markers']
markers = [
    {'size': 1},
    {'size': 1},
    {'size': 1},
    {'size': 10},
]

fig_2 = go.Figure()
for i in range(len(y_values)):
    fig_2.add_trace(go.Scatter(x=x_values, y=y_values[i], mode=modes[i],
                               marker=markers[i], name=columns[i]))
    # fig_2.add_trace(go.Scatter(x=x_values, y=data['U1_averaged'],
    #                            mode='markers'))
fig_2.update_layout(
    font_family="Arial",
    font_color="black",
    font_size=14,

)
fig_2.update_xaxes(title="DateTime")
fig_2.update_yaxes(title="Value")
fig_2.show()






