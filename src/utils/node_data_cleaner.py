import pandas as pd 
import re
from csv_splitter import csv_splitter

data = pd.read_excel('data-all/original/NODE_03Sept2025.xlsx')
references = pd.read_csv('data-all/original/NODE_reference_list.tsv',
                         sep='\t', 
                         usecols=['NODE FULL REFERENCES', 'NODE REFERENCE CITATIONS'])
data = data.merge(references, left_on='REFERENCE', right_on='NODE REFERENCE CITATIONS', how='left') 
data.columns = data.columns.str.lower()

# PIs and Collectors
data['node full references'] = data['node full references'].str.replace(r'(?<=\b)[Il](?=\d)', "1", regex=True)
data['pi'] = data['node full references'].str.extract(r'^(.*?)(?:\s+\d{4}|\s+unpublished data)',
                                                           flags=re.IGNORECASE)
data['pi'] = data['pi'].str.strip().str.replace(r'\s+', ' ', regex=True)

data['pi'] = data['pi'].str.replace(r'&', '|', regex=True)
data['pi'] = data['pi'].str.replace(r'\.,', '. |', regex=True)
data['pi'] = data['pi'].str.replace(r'(\.)\s*,\s*(?=[A-Z])', r'\1| ', regex=True)
data['pi'] = data['pi'].str.replace(r'\s+et al\.?$', '', regex=True)
data['pi'] = data['pi'].str.replace(r'\s+and\s+', '|', regex=True)
data['pi'] = data['pi'].str.strip()
data['pi'] = data['pi'].str.strip("|")

# Site Data
data['longitude'] = round(data['londeg'] + data['lonmin'] / 60 + data['lonsec'] / 3600, 6)
data['latitude'] = round(data['latdeg'] + data['latmin'] / 60 + data['latsec'] / 3600, 6)
data['sitename'] = data['locality'].fillna('') + ', ' + data['site'].fillna('')
data['sitename'] = data['sitename'].str.strip(', ')
data['sitename'] = data['sitename'].str.strip()
data = data.assign(**{'sample_analyst': 'Horne, David',
                      'dataset_processor': 'Horne, David'})

# CU
data = data.rename(columns = {'year': 'taxonname_year',
                              'field23': 'year'})
data.loc[data['month'].notna() & data['year'].notna() & data['day'].isna(), 'day'] = 1
data['collection_date'] = pd.to_datetime(data[["year", "month", "day"]], errors='coerce')
data["collection_date"] = data["collection_date"].dt.strftime("%Y-%m-%d")
data = data.rename(columns={'year': 'collectionyear'})
data['collection_date'] = data['collection_date'].fillna(data['collectionyear'])

# Record Data
data['record_number'] = 'NODE-R' + (
    data.groupby(['longitude', 'latitude', 'sitename', 
                  'collectionyear', 'node full references'], 
                 dropna=False).ngroup().add(1).astype(str))
data['handle_complete'] = data['record_number']

# Taxon Data
data['taxonname'] = data['taxonname'] = data['genus'].str.strip() + ' ' + data['species'].str.strip()
data['taxonname'] = data['taxonname'].str.replace('  ', ' ')
# regex = r'^(\w+(?:\s+\w+)?)'
# data['taxonname'] = data['taxonname'].astype(str).str.extract(regex)

data['count'] = 'presence/absence'
data['value'] = 1
data['variableelement'] = 'valve (undiff)'
data['context'] = 'live'

# Habitat Data
data['natural habitat'] = data['natural habitat'].fillna(data['artificial habitat'])

# Clean columns
data.drop(columns=['artificial habitat',
                   'londeg', 'lonmin', 'lonsec',
                   'latdeg', 'latmin', 'latsec',
                   'reference', 'node reference citations'], inplace=True)

data['natural habitat'] = data['natural habitat'].str.replace(r'lake', 'lacustrine', flags=re.IGNORECASE)
data = data.rename(columns={'natural habitat': 'habitat',
                            'name in ref': 'name in publication',
                            'node full references': 'citation',
                            'age': 'age of waterbody',
                            'combo403': 'coord validation'})

# Add missing data
data['collection_type'] = 'modern'
data['age_model'] = 'Collection Date'
data['age_type'] = 'Calendar years BP'

data = data.rename(columns={'temp': 'temperature',
                            'ph': 'pH'})

def notes_parser(row, sep=" | "):
    parts = []
    for col in comment_cols:
        value = row[col]
        if pd.notnull(value):  # skip NaN
            parts.append(f"{col.capitalize()}: {value}")
    return sep.join(parts)

comment_cols = ['comments', 'cond', 'duration', 'temperature', 
                'vegetation', 'water chemistry', 'zone of coll',
                'pH', 'age of waterbody', 'environment']
data['datasetnotes'] = data.apply(notes_parser, axis=1)

comment_cols = ['name in publication', 'subspecies', 'sex ratio', 'males?']
data['datasetnotes2'] = data.apply(notes_parser, axis=1, sep="; ")

comment_cols = ['coord validation']
data['collunitnotes'] = data.apply(notes_parser, axis=1)
columns = [
    # Site
    'record_number', 'sitename', 'longitude', 'latitude', 'altitude',
    # CU
    'handle_complete', 'habitat', 'water chemistry', 'depth', 'collection_type', 
    'collunitnotes', 'substrate', 'vegetation', 'pH', 'temperature', 'cond', 
    'environment', 'duration', 'collection_date', 'age of waterbody', 'datasetnotes',
    'datasetnotes2',
    # Chronologies
    'age_model', 'age_type',
    # Publications
    'citation',
    # GPU
    'country', 'region', 'site', 'locality', 'day', 'month', 'collectionyear',
    # Taxa
    'taxonname', 'taxonname_year', 'count', 'value', 'variableelement',
    'context', 'name in publication',
    # Contacts
    'pi', 'sample_analyst', 'dataset_processor'
]
data = data[columns]
data.sort_values(by=['record_number'], inplace=True)
data.to_excel('data-all/original/NODE-cleanedSep2025.xlsx', index=False)

csv_splitter(data, params='record_number')