import pandas as pd
import numpy as np
import ast
import yaml

#df = pd.read_excel('GOOD_template_spreadsheet.xlsx')
# Add InLineList to create vocab as a list in yml file
class InlineList:
    def __init__(self, data):
        self.data = data

def represent_inline_list(dumper, data):
    return dumper.represent_sequence(u'tag:yaml.org,2002:seq', data.data, flow_style=True)

yaml.add_representer(InlineList, represent_inline_list)


def excel_to_yaml(temp_file, file_name):
    # Template info
    df1 = pd.read_excel(temp_file, sheet_name= 'Data Mapping')
    df1 = df1[df1['Column']!="—NA—"]
    df1 = df1.replace({np.nan: None})
    df1.columns = map(str.lower, df1.columns)
    df1['vocab'] = df1['vocab'].str.replace("'", '"')
    df1['vocab'] = df1['vocab'].str.replace("‘", '"')
    df1['vocab'] = df1['vocab'].str.replace("’", '"')
 
    # Metadata
    df2 = pd.read_excel(temp_file, sheet_name= 'Metadata')
    df2 = df2[df2['Column']!="—NA—"]
    df2 = df2.replace({np.nan: None})
    df2.columns = map(str.lower, df2.columns)

    # Setting the dictionary
    data = df1.groupby(['column', 'neotoma']).apply(lambda x: x.to_dict(orient='index')).to_dict() 
    metadata = df2.to_dict(orient='records')

    data_list = []
    for key, value in data.items():
        data_list.append(list(value.values())[0])

    units_entries = list()
    uncertainty_units_entries = list()
    uncertainty_entries = list()
    for entry in data_list:
        if entry['unitcolumn'] is None:
            del entry['unitcolumn']
        else:
            units_dict = {'column': entry['unitcolumn'],
                        'neotoma': 'ndb.variableunits.variableunits',
                        'required': False,
                        'rowwise': True,
                        'type': 'string',
                        'vocab': entry['vocab']}
            units_entries.append(units_dict)
        if entry['uncertaintycolumn'] is None:
            del entry['uncertaintycolumn']
            del entry['uncertaintybasis']
            del entry['uncertaintyunitcolumn']
        else:
            entry['uncertainty'] = {'uncertaintycolumn': entry['uncertaintycolumn'], 
                                    'uncertaintybasis': entry['uncertaintybasis'], 
                                    'unitcolumn': entry['uncertaintyunitcolumn']}     
            uncertainty_dict = {'column': entry['uncertaintycolumn'],
                                'formatorrange': entry['formatorrange'],
                                'neotoma': 'ndb.values',
                                'required': False,
                                'rowwise': True,
                                'taxonid': entry['taxonid'],
                                'taxonname': entry['taxonname'],
                                'type': entry['type'],
                                'vocab': None}
            uncertainty_entries.append(uncertainty_dict)
            del entry['uncertaintycolumn']
            del entry['uncertaintybasis']
            uncertainty_unit_dict = {'column': entry['uncertaintyunitcolumn'],
                        'neotoma': 'ndb.values',
                        'notes': entry['notes'],
                        'required': False,
                        'rowwise': True,
                        'type': entry['type'],
                        'vocab': entry['vocab']}
            uncertainty_units_entries.append(uncertainty_unit_dict)
            del entry['uncertaintyunitcolumn']       
        if entry['vocab'] is None:
            del entry['vocab']
        else:
            if isinstance(entry['vocab'], str) and entry['vocab'].startswith('[') and entry['vocab'].endswith(']'):
                # Handling strings of lists for the YML
                try:
                    entry['vocab'] = ast.literal_eval(entry['vocab'])
                    entry['vocab'] = InlineList(entry['vocab'])
                except (ValueError, SyntaxError):
                    # Leave it as is
                    pass
        if entry['formatorrange'] is None:
            del entry['formatorrange']
        if entry['constant'] is None:
            del entry['constant']
        if entry['taxonname'] is None:
            del entry['taxonname']
        if entry['taxonid'] is None:
            del entry['taxonid']
        if entry['notes'] is None:
            del entry['notes']

    # Joining it all
    data_list = data_list + units_entries + uncertainty_entries + uncertainty_units_entries
    data_list = sorted(data_list, key=lambda x: x['column'])
    data_list = metadata + data_list

    final_dict = {'apiVersion': 'neotoma v2.0',
                'headers': 2,
                'kind': 'Development',
                'metadata': data_list}

    file_name = file_name + '.yml'
    with open(file_name, "w") as f:
        yaml.dump(final_dict, f)
        
    return None