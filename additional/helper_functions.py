import pandas as pd
import numpy as np
from rich import print
import pymongo


def testbench_formats(name:  str) -> (str, str):
    """
    Determines the column set ID and datetime format based on the given
    testbench name. This function maps specified testbench names to a
    corresponding column set identifier and a datetime format string. If
    an unsupported name is provided, a ValueError is raised.

    :param name: The name of the testbench. Supported names include
        'BZ_3Gleiche', 'BZ011', and 'BZ016'.
    :type name: str
    :return: A tuple containing the column set ID and the datetime format
        string corresponding to the given testbench name.
    :rtype: tuple[str, str]
    :raises ValueError: If the provided testbench name is not supported.
    """
    if name == 'BZ_3Gleiche':
        col_set_id = 103
        datetime_format = "%d.%m.%y %H:%M:%S"
    elif name == 'BZ011':
        col_set_id = 2
        datetime_format = "%d.%m.%y %H:%M:%S"
    elif name == 'BZ016':
        col_set_id = 127
        # Still need to check if this works, I'm confused by a two decimal
        # place "millisecond"?
        datetime_format = "%d.%m.%Y %H:%M:%S,%f"
    else:
        raise ValueError('Testbench name not found')
    return col_set_id, datetime_format


def determine_column_actions(file_path):
    """
    Determines the column actions from a specific sheet in an Excel file. This
    function reads the "header" sheet in the Excel file provided via the
    file_path to extract column metadata or actions from the first row and
    returns it as a dictionary.

    :param file_path: The file path to the Excel file to be processed.
    :type file_path: str
    :return: A dictionary representing column actions extracted from the "header"
        sheet of the provided Excel file. Each dictionary entry can be
        0: neglect column,
        1: process column,
        2: visualize column,
    :rtype: dict
    """
    xls_file = pd.ExcelFile(file_path)
    # Set dataframes mit Filter
    column_actions = pd.read_excel(xls_file, 'header',
                                   nrows=1).to_dict('records')[0]
    return column_actions

def determine_processing_parameters(file_path):
    """
    Determines the processing parameters from a given Excel file. The function reads
    the specified Excel file, navigates to the sheet named 'filter', and processes
    the data to extract processing parameters into a dictionary format. This
    dictionary is indexed by 'setID' and contains corresponding values from the
    sheet's data.

    :param file_path: The file path to the Excel file containing processing method
        information, expected to have a sheet named 'filter' with relevant data.
    :type file_path: str
    :return: A dictionary with 'setID' as keys and the corresponding data from the
        'filter' sheet as values.
    :rtype: dict
    """
    xls_file = pd.ExcelFile(file_path)
    # Set dataframes mit Filter
    processing_methods = (
        pd.read_excel(xls_file, 'filter').set_index('setID').to_dict('index'))
    return processing_methods


def count_continuous_sections(data_frame: pd.DataFrame, column: str,
                              change_count_name: str = 'change_count'):
    set_change = data_frame[column].diff().fillna(0)
    set_change = set_change.astype('int')
    set_change[set_change != 0] = 1
    data_frame['change_count'] = set_change.cumsum()
    return data_frame


def add_columns_to_existing_collection(
        data_frame: pd.DataFrame, mongo_client: pymongo.MongoClient,
        db_name: str, coll_name: str, datetime_str: str):

    # Convert the dataframe to a dictionary format for MongoDB insertion
    df_dict = data_frame.to_dict(orient='records')
    # Insert the dataframe into a new collection for merging (temp collection)
    db = mongo_client[db_name]

    if "new_data" in db.list_collection_names():
        db.drop_collection("new_data")
    # Create temporary time-series collection if it doesn't exist
    db.create_collection(
        "new_data",
        timeseries={
            "timeField": datetime_str,
            "metaField": "metadata",
            "granularity": "seconds"
        },
    )
    db["new_data"].insert_many(df_dict)

    # Perform the merge operation using $lookup
    pipeline = [
        {
            "$lookup": {
                "from": "new_data",
                "localField": "_id",
                "foreignField": "_id",
                "as": "added_fields"
            }
        },
        {
            # Flatten the array (removes users with no orders)
            "$unwind": "$added_fields"
        },
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$$ROOT", "$added_fields"]}
            }
        },
        {
            # Remove the redundant merged object
            "$project": {"added_fields": 0}
        },
        {
            "$merge": {
                # Save result in new collection
                "into": "merged_collection",
                # Update existing documents if IDs match
                "whenMatched": "merge",
                # Insert new documents if not present
                "whenNotMatched": "insert"
            }
        }
    ]
    db[coll_name].aggregate(pipeline)
    db.drop_collection("new_data")

def remove_non_numeric_columns(data_frame: pd.DataFrame):

    # Separate numeric and non-numeric columns
    numeric_columns = (
        data_frame.select_dtypes(include=np.float64).dropna(axis=1)).columns.tolist()
    # non_numeric_columns = [name for name in data_frame.columns
    #                        if name not in numeric_columns]
    # df_non_numeric = data_frame[non_numeric_columns]
    df_numeric = data_frame[numeric_columns]
    return df_numeric

def processing_function(data_frame: pd.DataFrame):
    pass



test_file_path = "./filters/Filter_BZ011.xlsx"

test = determine_processing_parameters(test_file_path)
