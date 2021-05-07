import logging


class Config():
    input_folder = 'input/NL'
    output_folder = 'output'

    main_column = "Destination"
    main_column_exclude = "14-karaat\/|8-karaat\/|9-karaat\/|18-karaat\/|22-karaat\/|500\/|585\/|600\/|950\/|925\/"

    secondary_column = "Anchor"
    secondary_column_exclude = "Ja|Nee|Breedte|Kleur|Gehalte|Profiel|Prijs|Steengrotte|Stijl|Menu|Account|Seite Zurück|Pagina Vorige|Verwijder dit artikel"

    # In the following format: "Column name": "list|of|possible|values" (uses pandas.Series.str.fullmatch)
    additional_filters = {
        "Follow": "true|false"
    }

    # Merge index cells (True) or write the text into each column (False)
    merge_output_cells = False

    # logging
    logger = logging.getLogger('Pivot_table_script')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('pivot_table.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
