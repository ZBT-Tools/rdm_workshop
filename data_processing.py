import pandas as pd
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
import helper_functions as hf
from rich import print
import plotly.express as px

# Retrieve complete data set processing control directives from xlsx file
processing_control_file = "./filters/Filter_BZ011.xlsx" #spezifisch fürs
processing_parameters_dict = hf.determine_processing_parameters(
    processing_control_file)
column_actions = hf.determine_column_actions(processing_control_file)

# Choose test bench
testbench_list = ['BZ011', 'BZ016', 'BZ_3Gleiche']
testbench_name = 'BZ011'

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
client = MongoClient(host=mongodb_ip, port=27017, username=mongodb_user,
                     password=mongodb_password, authSource="admin",
                     directConnection=True)

# Select database and collection
db = client["rdm_workshop"]
collection = db["BZ011_Rohdaten"]

# Fetch all data from MongoDB collection
cursor = collection.find({})  # Empty filter `{}` fetches all documents
# Convert to DataFrame and sort by datetime column
df_full = pd.DataFrame(list(cursor)).sort_values(["Datum"])

fig_1 = px.line(df_full, x='Datum', y=['p_Luft/bar_ein', 'T_Luft_ein',
                                     'Set aktuell'])
# fig_1.show()

# Processing columns
process_columns = [name for name, value in column_actions.items() if value == 1]
# Fetch only entries with specific set number
set_id = 13
cursor = collection.find({'Set aktuell': {'$eq': set_id}})
# Create a dataframe based on the specified set_id and the list of columns to
# be processed and sort the dataframe by the key "Datum"
df_subset = pd.DataFrame(list(cursor)).sort_values(['Datum'])[process_columns]
processing_parameters = processing_parameters_dict[set_id]
method_key = 'Auswertemodus (c: zyklisch / lv: last value)'
method = processing_parameters[method_key]
# method = 'lv'

averaging_size = processing_parameters['avgN']

# Separate numeric and non-numeric columns
numeric_columns = (
    df_subset.select_dtypes(include=np.float64).dropna(axis=1)).columns.tolist()
non_numeric_columns = [name for name in df_subset.columns
                       if name not in numeric_columns]
df_subset_non_numeric = df_subset[non_numeric_columns]
df_subset_numeric = df_subset[numeric_columns]

# if method == 'c':
# Apply a rolling average over the dataframe
df_processed = df_subset_numeric.rolling(averaging_size).mean()
# Take only every nth value
# df_processed = df_processed.shift(periods=-1)
df_processed = df_processed.iloc[::averaging_size].iloc[1:]
# df_processed = (
#     df_subset_numeric.groupby(np.arange(len(df_subset_numeric)) //
#                               averaging_size).mean())
if method == 'lv':
    # Apply averaging only to last n values
    df_processed = df_processed.iloc[-1]
df_subset['']


fig_2 = px.line(df_processed, x='Datum')
fig_2.show()






