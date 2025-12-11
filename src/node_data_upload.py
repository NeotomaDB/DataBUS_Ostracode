import json
import os
import psycopg2
import glob
from datetime import datetime
from dotenv import load_dotenv
import DataBUS.neotomaHelpers as nh
import DataBUS.neotomaUploader as nu
from DataBUS.neotomaValidator.check_file import check_file
from DataBUS.neotomaHelpers.logging_dict import logging_response

"""
Use this command after having validated the files to 
upload to Neotoma.
To run, you can use: 
python template_upload.py

In that case, the default template 'template.yml' is used.

You can also use a different template file by running:
python src/node_data_upload.py --template='src/templates/node_template.yml' --data='data/NODE/' --validation_logs='data/NODE/validation_logs/'

Change 'template_xlsx.xlsx' to desired filename as long as 
template file that has an .xlsx or .yml extension
"""

load_dotenv()
data = json.loads(os.getenv('PGDB_TANK'))

conn = psycopg2.connect(**data, connect_timeout = 5)
cur = conn.cursor()

args = nh.parse_arguments()
overwrite = args['overwrite']

valid_logs = 'data/NODE/validation_logs/'
filenames = glob.glob(args['data'] + "*.csv")
upload_logs = 'data/NODE/upload_logs' 
if not os.path.exists(upload_logs):
            os.makedirs(upload_logs)
uploaded_files = "data/NODE/uploaded_files"

total_files = len(filenames)
start_time = datetime.now()
print(f"Start uploading {total_files} files at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
next_percent = 5

#filenames = ['data/NODE/NODE-R144.csv']
for j, filename in enumerate(filenames, 1):
    test_dict = {}
    print(filename)
    logfile = []

    hashcheck = nh.hash_file(filename, valid_logs)
    filecheck = check_file(filename, validation_files=valid_logs, strict=False) # Will not allow changes in the database.

    logfile = logfile + hashcheck['message'] + filecheck['message']
    logfile.append(f"\nNew Upload started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if hashcheck['pass'] is False and filecheck['pass'] is False:
        csv_file = nh.read_csv(filename)
        logfile.append("File must be properly validated before it can be uploaded.")
    else:
        csv_file = nh.read_csv(filename)
        # This possibly needs to be fixed. How do we know that there is one or more header rows?

    uploader = {}
 
    yml_dict = nh.template_to_dict(temp_file=args['template'])
    yml_data = yml_dict['metadata']
    inputs = {'cur': cur,
              'yml_dict': yml_dict,
              'csv_file': csv_file}
    try:
        conn.rollback()
        logfile.append('\n=== Inserting New Site ===')
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
        
        logfile.append('\n=== Inserting Dataset ===')
        uploader['datasets'] = nu.insert_dataset(**inputs)
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
 
        logfile.append('\n === Inserting Data ===')
        uploader['data'] = nu.insert_data(**inputs)
        logfile = logging_response(uploader['data'], logfile)

        logfile.append('\n === Uploading Publications ===')
        uploader['publications'] = nu.insert_publication(**inputs)
        logfile = logging_response(uploader['publications'], logfile)

        logfile.append('\n === Finalizing Insert  ===')
        uploader['finalize'] = nu.insert_final(cur, 
                                               uploader = uploader)
        all_true = all([uploader[key].validAll for key in uploader])
        all_true = all_true and hashcheck

        if all_true:
            print(f"{filename} was uploaded.\nMoved {filename} to the 'uploaded_files' folder.")
            #conn.commit()
            conn.rollback()
            os.makedirs(uploaded_files, exist_ok=True)
            uploaded_path = os.path.join(uploaded_files, os.path.basename(filename))
            os.replace(filename, uploaded_path)
            modified_filename = filename.replace('data/NODE/', 'data/NODE/upload_logs/')
            with open(modified_filename + '.upload.log', 'w', encoding = "utf-8") as writer:
                for i in logfile:
                    writer.write(i)
                    writer.write('\n')
        else:
            not_uploaded_files = "data/NODE/failed_uploads"
            os.makedirs(not_uploaded_files, exist_ok=True)
            not_uploaded_path = os.path.join(not_uploaded_files, os.path.basename(filename))
            os.replace(filename, not_uploaded_path)
            print(f"filename {filename} could not be uploaded.")
            os.makedirs('data/NODE/upload_logs/failed_uploads/', exist_ok=True)
            modified_filename = filename.replace('data/NODE/', 'data/NODE/upload_logs/failed_uploads/')
            with open(modified_filename + '.upload.log', 'w', encoding = "utf-8") as writer:
                for i in logfile:
                    writer.write(i)
                    writer.write('\n')
            conn.rollback()
    except Exception as e:
        print(e)
        not_uploaded_files = "data/NODE/failed_uploads"
        logfile.append(f"✗ File upload failed: {e}")
        os.makedirs(not_uploaded_files, exist_ok=True)
        not_uploaded_path = os.path.join(not_uploaded_files, os.path.basename(filename))
        os.replace(filename, not_uploaded_path)
        print(f"filename {filename} could not be uploaded: {e}.")
        conn.rollback()
        os.makedirs('data/NODE/upload_logs/failed_uploads/', exist_ok=True)
        modified_filename = filename.replace('data/NODE/', 'data/NODE/upload_logs/failed_uploads/')
        with open(modified_filename + '.upload.log', 'w', encoding = "utf-8") as writer:
            for i in logfile:
                writer.write(i)
                writer.write('\n')
    finally:
         ### Temporary to check how many files are pending
        percent_complete = (j / total_files) * 100
        if percent_complete >= next_percent:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"Uploaded {next_percent}% at {now}")
            next_percent += 5
end_time = datetime.now()
print(f"Finished uploading at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")