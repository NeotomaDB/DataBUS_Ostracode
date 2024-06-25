import logging
import neotomaHelpers as nh

def insert_dataset_database(cur, yml_dict, uploader):
    """
    Inserts dataset and database associations into Neotoma

    Args:
        cur (cursor object): Database cursor to execute SQL queries.
        yml_dict (dict): Dictionary containing YAML data.
        uploader (dict): Dictionary containing uploader details.

    Returns:
        response (dict): A dictionary containing information about the dataset-database insertion.
            - 'databaseid' (int): ID of the associated database or NaN if not available.
            - 'valid' (bool): Indicates if the insertion was successful.
    """
    response = {'databaseid': None, 'valid': list(), 'message': list()}
    db_query = """
               SELECT ts.insertdatasetdatabase(_datasetid := %(datasetid)s, 
                                               _databaseid := %(databaseid)s)
               """
    inputs = dict()
    db_name = nh.retrieve_dict(yml_dict, 'ndb.datasetdatabases.databaseid')
    inputs['databaseid'] = db_name[0]['value']

    try:
        cur.execute(db_query, {'datasetid': int(uploader['datasetid']['datasetid']), 
                               'databaseid': int(inputs['databaseid'])})
        response['valid'].append(True)
        response['message'].append(f"✔ Database ID {inputs['databaseid']} information added.")

    except Exception as e:
        logging.error(f"✗ Database information is not correct. {e}")
        response['message'].append(f"✗ Database information is not correct. {e}")
        cur.execute(db_query, {'datasetid': int(uploader['datasetid']['datasetid']), 
                            'databaseid': None})
        response['message'].append(f"✗ Using temporary query.")
        response['valid'] = False
    response['databaseid'] = inputs['databaseid']
    response['valid'] = all(response['valid'])
    return response