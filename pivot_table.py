import argparse
import importlib
import os
import subprocess
import sys
from typing import List, Any

# Install missing libraries if necessary
try:
    import openpyxl
    import pandas as pd
    import numpy as np
    from pandas import DataFrame
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    import pandas as pd
    import numpy as np
    from pandas import DataFrame


def read_input_csv_files(input_folder: str) -> List[Any]:
    """ Collect full paths of csv files inside the input folder provided by config. """
    input_files = list()
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            filename, extension = os.path.splitext(file)
            if extension == '.csv':
                full_file_path = os.path.abspath(os.path.join(root, file))
                input_files.append(full_file_path)
    return input_files


def get_new_output_path(original_file_path: str, config):
    """ Construct new file path in the same subdirectory as the original file,
        but inside the output folder instead of the input one,
        and with .xlsx extension instead of .csv
    """
    file_subdirectory = os.path.relpath(os.path.dirname(original_file_path), config.input_folder)
    filename, extension = os.path.splitext(os.path.basename(original_file_path))
    new_file_name = ''.join((filename, '.xlsx'))
    new_file_path = os.path.join(config.output_folder, file_subdirectory, new_file_name)
    return new_file_path


def write_dataframe_to_output(dataframe: DataFrame, original_file_path: str, config):
    new_file_path = get_new_output_path(original_file_path, config)
    dataframe.to_excel(new_file_path, merge_cells=config.merge_output_cells)


def filter_dataframe(dataframe: DataFrame, config) -> DataFrame:
    """ Filter dataframe according to the provided config.
        Main and secondary columns filter out any values that fit 'pandas.Series.str.contains',
        additional filters use a different filter: 'pandas.Series.str.fullmatch',
        and are including rather than excluding.
    """
    # drop empty columns
    dataframe = dataframe.dropna(how='all', axis=1)
    # Filter main column
    if config.main_column_exclude:
        dataframe = dataframe[~dataframe[config.main_column].str.contains(config.main_column_exclude, na=False)]
    # Filter secondary column
    if config.secondary_column_exclude:
        dataframe = dataframe[~dataframe[config.secondary_column].str.contains(config.secondary_column_exclude, na=False)]

    dataframe = dataframe.fillna('').astype(str)  # for string-based filtering
    for filter_column, filter_values in config.additional_filters.items():
        try:
            dataframe = dataframe[dataframe[filter_column].str.fullmatch(filter_values)]
        except KeyError:
            config.logger.error(f'Couldn\'t find column {filter_column} in the dataframe, skipping filter.')
            continue  # No such column, skipping filter
    return dataframe


def pivot_table(dataframe: DataFrame, config) -> DataFrame:
    """
    Create a pivot table out of provided dataframe by dropping all columns and counting
    distinct combinations of main and secondary columns, provided in config.
    """
    index_columns = [config.main_column, config.secondary_column]
    new_df = dataframe.drop(dataframe.columns.difference(index_columns), 1)
    # drop rows where secondary column is empty
    new_df = new_df[new_df[config.secondary_column].str.strip().astype(bool)]

    count_column = f'Count of {config.secondary_column}'
    new_df[count_column] = 1

    pivot_dataframe = new_df.pivot_table(
        index=index_columns,
        values=[count_column],
        aggfunc=np.count_nonzero,
    )
    return pivot_dataframe


def pivot_chunked_file(input_file_path: str, config) -> DataFrame:
    """ Create a pivot table of the provided file according to config.
        This function uses chunked mode, where a separate pivot table is created for each chunk,
        and then gets merged with the pivot table of the next chunk.
    """
    reader = pd.read_csv(input_file_path, dtype=str, chunksize=100000, na_filter=False)
    overall_pivot_df = None

    for chunk in reader:
        filtered_chunk = filter_dataframe(dataframe=chunk, config=config)
        pivot_chunk = pivot_table(dataframe=filtered_chunk, config=config)
        if pivot_chunk.empty:  # Zero non-null rows, nothing to merge
            continue
        if overall_pivot_df is None:
            overall_pivot_df = pivot_chunk
        else:
            count_column = overall_pivot_df.columns[0]
            overall_pivot_df = pd\
                .merge(overall_pivot_df, pivot_chunk, left_index=True, right_index=True, how='outer')\
                .sum(axis=1)\
                .rename(count_column)\
                .to_frame()
    return overall_pivot_df


def pivot_file(input_file_path: str, config) -> DataFrame:
    """ Create a pivot table of the provided file according to config.
        File is first read into the dataframe, then filtered and a pivot table is created.
        If the file is too large to read at once, a more complex pivot_chunked_file function is used.
    """
    MAX_FILE_SIZE = 100 << 20  # 100 megabytes
    if os.path.getsize(input_file_path) > MAX_FILE_SIZE:  # File is too big to read at once
        pivot_df = pivot_chunked_file(input_file_path=input_file_path, config=config)
    else:
        df = pd.read_csv(input_file_path, dtype=str)
        filtered_df = filter_dataframe(dataframe=df, config=config)
        pivot_df = pivot_table(dataframe=filtered_df, config=config)
    return pivot_df


def main():
    parser = argparse.ArgumentParser(
        description='Pivot table creating script, making .xlsx files out of dataframes read from csv files.',
        usage='python comparing_script.py [-c config_file.py]'
    )
    parser.add_argument('-c', dest='config', default='config.py', help='[optional] path to config file.')
    options = parser.parse_args()

    # config import
    if not os.path.isfile(options.config):
        raise ModuleNotFoundError('Couldn\'t find config file at the provided path')
    config_module = importlib.import_module(os.path.splitext(options.config)[0])
    config = getattr(config_module, 'Config')

    config.logger.info(f'Starting script using config {options.config}')
    input_files = read_input_csv_files(input_folder=config.input_folder)
    config.logger.debug(f'Discovered {len(input_files)} files in the input folder: {input_files}')

    for input_file_path in input_files:
        try:
            config.logger.debug(f'Processing file {input_file_path}')
            pivot_df = pivot_file(input_file_path=input_file_path, config=config)
            write_dataframe_to_output(dataframe=pivot_df, original_file_path=input_file_path, config=config)
        except ZeroDivisionError:
            config.logger.exception(f'Uncaught exception while parsing file {input_file_path}: ')
    config.logger.info('Closing script')


if __name__ == "__main__":
    main()
