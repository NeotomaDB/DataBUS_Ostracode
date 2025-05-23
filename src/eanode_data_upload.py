import json
import os
import psycopg2
import glob
from datetime import datetime
from dotenv import load_dotenv
import DataBUS.neotomaHelpers as nh
import DataBUS.neotomaUploader as nu
from DataBUS.neotomaValidator.valid_csv import valid_csv
from DataBUS.neotomaValidator.check_file import check_file
from DataBUS.neotomaHelpers.logging_dict import logging_response

"""
Use this command after having validated the files to 
upload to Neotoma.
To run, you can use: 
python template_upload.py

In that case, the default template 'template.yml' is used.

You can also use a different template file by running:
python src/eanode_data_upload.py --template='src/templates/eanode_template.yml'

Change 'template_xlsx.xlsx' to desired filename as long as 
template file that has an .xlsx or .yml extension
"""

load_dotenv()
data = json.loads(os.getenv('PGDB_LOCAL'))

conn = psycopg2.connect(**data, connect_timeout = 5)
cur = conn.cursor()

args = nh.parse_arguments()
overwrite = args['overwrite']

filenames = glob.glob(args['data'] + "*.csv")
upload_logs = 'data/upload_logs'
if not os.path.exists(upload_logs):
            os.makedirs(upload_logs)

uploaded_files = "data/uploaded_files"

for filename in filenames:
    test_dict = {}
    print(filename)
    logfile = []

    hashcheck = nh.hash_file(filename)
    filecheck = check_file(filename, strict=False) # Will not allow changes in the database.

    logfile = logfile + hashcheck['message'] + filecheck['message']
    logfile.append(f"\nNew Upload started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if hashcheck['pass'] is False and filecheck['pass'] is False:
        csv_file = nh.read_csv(filename)
        logfile.append("File must be properly validated before it can be uploaded.")
    else:
        csv_file = nh.read_csv(filename)

    uploader = {}
 
    yml_dict = nh.template_to_dict(temp_file=args['template'])
    yml_data = yml_dict['metadata']
    inputs = {'cur': cur,
            'yml_dict': yml_dict,
            'csv_file': csv_file}
    
    try:
        logfile.append('\n=== Inserting Site ===')
        uploader['sites'] = nu.insert_site(**inputs)
        logfile = logging_response(uploader['sites'], logfile)

        inputs.update({'uploader': uploader})
        logfile.append('\n === Inserting Site-Geopolitical Units ===')
        uploader['geopol_units'] = nu.insert_geopolitical_units(**inputs)
        logfile = logging_response(uploader['geopol_units'], logfile)

        logfile.append('\n === Inserting Collection Units ===')
        uploader['collunitid'] = nu.insert_collunit(**inputs)
        logfile = logging_response(uploader['collunitid'], logfile)

        logfile.append('\n=== Inserting Collector ===')
        uploader['collector'] = nu.insert_collector(**inputs)
        logfile = logging_response(uploader['collector'], logfile)

        logfile.append('\n=== Inserting Analysis Units ===')
        uploader['anunits'] = nu.insert_analysisunit(**inputs)
        logfile = logging_response(uploader['anunits'], logfile)    

        logfile.append('\n=== Inserting Chronology ===')
        uploader['chronology'] = nu.insert_chronology(**inputs)
        logfile = logging_response(uploader['chronology'], logfile)

        logfile.append('\n=== Inserting Dataset ===')
        uploader['datasets'] = nu.insert_dataset(**inputs, name="Name in record")
        logfile = logging_response(uploader['datasets'], logfile)

        logfile.append('\n=== Inserting Dataset PI ===')
        uploader['datasetpi'] = nu.insert_dataset_pi(**inputs)
        logfile = logging_response(uploader['datasetpi'], logfile)
        
        logfile.append('\n=== Inserting Data Processor ===')
        uploader['processor'] = nu.insert_data_processor(**inputs)
        logfile = logging_response(uploader['processor'], logfile)

        logfile.append('\n=== Inserting Dataset Database ===')
        uploader['database'] = nu.insert_dataset_database(cur = cur,
                                                        yml_dict = yml_dict,
                                                        uploader = uploader)
        logfile = logging_response(uploader['database'], logfile)

        logfile.append('\n=== Inserting Samples ===')
        uploader['samples'] = nu.insert_sample(**inputs)
        logfile = logging_response(uploader['samples'], logfile)

        logfile.append('\n=== Inserting Sample Analyst ===')
        uploader['sampleAnalyst'] = nu.insert_sample_analyst(**inputs)
        logfile = logging_response(uploader['sampleAnalyst'], logfile)

        logfile.append('\n=== Validating Sample Ages ===')
        uploader['sample_age'] = nu.insert_sample_age(**inputs)
        logfile = logging_response(uploader['sample_age'], logfile)

        logfile.append('\n === Inserting Data ===')
        uploader['data'] = nu.insert_data(**inputs)
        logfile = logging_response(uploader['data'], logfile)

        logfile.append('\n === Uploading Publications ===')
        uploader['publications'] = nu.insert_publication(**inputs)
        logfile = logging_response(uploader['publications'], logfile)

        modified_filename = filename.replace('data/', 'data/upload_logs/')
        with open(modified_filename + '.upload.log', 'w', encoding = "utf-8") as writer:
            for i in logfile:
                writer.write(i)
                writer.write('\n')

        all_true = all([uploader[key].validAll for key in uploader])
        all_true = all_true and hashcheck['pass']
        if all_true:
            print(f"{filename} was uploaded.\nMoved {filename} to the 'uploaded_files' folder.")
            conn.commit()
            #conn.rollback()
            if not os.path.exists(uploaded_files):
                os.makedirs(uploaded_files)
            uploaded_path = os.path.join(uploaded_files, os.path.basename(filename))
            os.replace(filename, uploaded_path)

        else:
            print(f"filename {filename} could not be uploaded.")
            conn.rollback()
    except Exception as e:
        print(f"filename {filename} could not be uploaded.\n"
              f"Error: {e}")
        modified_filename = filename.replace('data/', 'data/upload_logs/')
        with open(modified_filename + '.upload.log', 'w', encoding = "utf-8") as writer:
            for i in logfile:
                writer.write(i)
                writer.write('\n')
        conn.rollback()