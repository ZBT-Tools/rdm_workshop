import pandas as pd
import numpy as np
from rich import print


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




test_file_path = "./filters/Filter_BZ011.xlsx"

test = determine_processing_parameters(test_file_path)