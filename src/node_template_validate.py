"""_Validate 210Pb csv Files_
   Assumes there is a `data` folder from which the python script is run.
   The script obtains all `csv` files in ./data and then reads through
   each of them, validating each field to ensure they are acceptable for
   valid upload.
"""
from datetime import datetime
import os
from pathlib import Path
import json
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import DataBUS.neotomaValidator as nv
import DataBUS.neotomaHelpers as nh
from DataBUS.neotomaHelpers.logging_dict import logging_dict, logging_response
from utils.valid_sample_age_ost import valid_sample_age_ost
from utils.valid_chronologies_ost import valid_chronologies_ost
from utils.valid_geopolitical_units import valid_geopolitical_units

"""
python src/node_template_validate.py --template='src/templates/node_template.yml' --data='data/NODE' --validation_logs='data/NODE/validation_logs/'
"""

args = nh.parse_arguments()
load_dotenv()
data = json.loads(os.getenv('PGDB_LOCAL'))
conn = psycopg2.connect(**data, connect_timeout = 5)
cur = conn.cursor()

directory = Path(args['data'])
filenames = directory.glob("*.csv")
valid_logs = 'data/NODE/validation_logs/'
valid_logs_wrong = Path('data/NODE/validation_logs/not_validated/')
Path(valid_logs).mkdir(exist_ok=True)
valid_logs_wrong.mkdir(exist_ok=True)

for filename in filenames:
    print(filename)
    logfile = []

    hashcheck = nh.hash_file(filename, valid_logs)
    filecheck = nv.check_file(filename, validation_files=valid_logs)

    logfile = logfile + hashcheck['message'] + filecheck['message']
    logfile.append(f"\nNew validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if hashcheck['pass'] and filecheck['pass']:
        print("  - File is correct and hasn't changed since last validation.")
    else:
        yml_dict = nh.template_to_dict(temp_file=args['template'])
        yml_data = yml_dict['metadata']
        validator = dict()
        csv_file = nh.read_csv(filename)
        
        # Get the unitcols and units to be used
        # Check that the vocab in the template matches the csv vcocab
        #vocab_ = nv.vocabDict(yml_data)

        logfile.append('\n=== File Validation ===')
        validator['csvValid'] = nv.valid_csv(filename = filename,
                                   yml_data = yml_data)
        logfile = logging_dict(validator['csvValid'], logfile)

        logfile.append('\n === Validating Template Unit Definitions ===')
        df = pd.read_csv(filename)
        validator['units'] = nv.valid_units(cur = cur,
                                 yml_dict = yml_dict,
                                 df = df)
        logfile = logging_dict(validator['units'], logfile)

        logfile.append('\n === Validating Sites ===')
        validator['sites'] = nv.valid_site(cur = cur,
                                 yml_dict = yml_dict,
                                 csv_file = csv_file)
        logfile = logging_response(validator['sites'], logfile)

        ## ADD GEOLOCALITY
        logfile.append('\n === Checking Against Geopolitical Units ===')
        validator['geopol_units'] = valid_geopolitical_units(cur = cur,
                                                   yml_dict = yml_dict,
                                                   csv_file = csv_file)
        logfile = logging_response(validator['geopol_units'], logfile)

        logfile.append('\n === Checking Against Collection Units ===')
        validator['collunits'] = nv.valid_collunit(cur = cur,
                                                   yml_dict = yml_dict,
                                                   csv_file = csv_file)
        logfile = logging_response(validator['collunits'], logfile)

        logfile.append('\n === Checking Against Analysis Units ===')
        validator['analysisunit'] = nv.valid_analysisunit(yml_dict = yml_dict,
                                                          csv_file = csv_file)
        logfile = logging_response(validator['analysisunit'], logfile)

        logfile.append('\n === Checking Dataset ===')
        validator['dataset'] = nv.valid_dataset(cur = cur,
                                                yml_dict = yml_dict,
                                                csv_file = csv_file)
        logfile = logging_response(validator['dataset'], logfile)

        logfile.append('\n === Checking Against Contact Names ===')
        validator['agent'] = nv.valid_contact(cur,
                                            csv_file,
                                            yml_dict)
        logfile = logging_response(validator['agent'], logfile)

        logfile.append('\n=== Validating Dataset Database ===')
        validator['database'] = nv.valid_dataset_database(cur = cur,
                                                        yml_dict = yml_dict)
        logfile = logging_response(validator['database'], logfile)

        logfile.append('\n=== Validating Samples ===')
        validator['sample'] = nv.valid_sample(cur = cur,
                                              yml_dict = yml_dict,
                                              csv_file = csv_file,
                                              validator = validator)
        logfile = logging_response(validator['sample'], logfile)

        # logfile.append('\n=== Validating Sample Ages ===')
        # validator['sample_age'] = valid_sample_age_ost(cur = cur,
        #                                       yml_dict = yml_dict,
        #                                       csv_file = csv_file,
        #                                       validator = validator)
        # logfile = logging_response(validator['sample_age'], logfile)
        
        logfile.append('\n === Validating Taxa Names ===')
        validator['taxa'] = nv.valid_data_long(cur = cur,
                                              yml_dict = yml_dict,
                                              csv_file = csv_file,
                                              validator = validator,
                                              filename=filename)
        logfile = logging_response(validator['taxa'], logfile)

        logfile.append('\n === Validating Publications ===')
        validator['publications'] = nv.valid_publication(cur, 
                                        yml_dict = yml_dict,
                                        csv_file = csv_file,
                                        validator = validator)
        logfile = logging_response(validator['publications'], logfile)

        # Nothing needs to be committed to the database
        conn.rollback()
        
        all_true = all([validator[key].validAll for key in ['sites', 'collunits', 'analysisunit',
                                                            'dataset', 'agent', 'database', 
                                                            'sample', 'taxa', 'publications']])

        not_validated_files = "data/NODE/not_validated_files"

        all_true = all_true and filecheck['pass']

        if all_true == False:
            print(f"{filename} cannot be validated.\nMoved {filename} to the 'not_validated_files' folder.")
            #os.makedirs(not_validated_files, exist_ok=True)
            #uploaded_path = os.path.join(not_validated_files, os.path.basename(filename))
            #os.replace(filename, uploaded_path)
            modified_filename = f'{filename}'.replace('data/NODE/', 'data/NODE/validation_logs/not_validated/')
            modified_filename = Path(modified_filename + '.valid.log')
        else:
            modified_filename = f'{filename}'.replace('data/NODE/', 'data/NODE/validation_logs/')
            modified_filename = Path(modified_filename + '.valid.log')
        
        with modified_filename.open(mode = 'w', encoding = "utf-8") as writer:
            for i in logfile:
                writer.write(i)
                writer.write('\n') 