import logging


class Config():
    input_folder = 'input/UK'
    output_folder = 'output'

    main_column = "Destination"
    main_column_exclude = "14-carat\/|8-carat\/|9-carat\/|18-carat\/|22-carat\/|500\/|585\/|600\/|950\/|925\/"

    secondary_column = "Anchor"
    secondary_column_exclude = "Yes|No|Colour|Purity|Width|Profile|Price|Stone size|Style|Menu|Account|Page Previous|Page Next|Remove This Item"

    # In the following format: "Column name": "list|of|possible|values" (uses pandas.Series.str.fullmatch)
    additional_filters = {
        "Follow": "FALSE",
    }

    # logging
    logger = logging.getLogger('Pivot_table_script')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('pivot_table.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
