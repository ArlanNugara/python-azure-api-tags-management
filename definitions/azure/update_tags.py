import requests
import json
import pandas as pd
import ast
import csv
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import load_workbook
from datetime import datetime
import time

# Get today's date
todays_date = datetime.today().strftime('%Y-%m-%d')

def update_tags_at_scope(main_url, scope, token_header):
  get_excel = pd.read_excel('tags.xlsx', sheet_name = scope, header=0)
  print("Scope Set to ", scope)
  tags_columns = ['Replace Tags', 'Merge Tags', 'Delete Tags']
  # Generate csv files
  for tag_column in tags_columns:
    target_columns = get_excel[['Scope', tag_column]]
    drop_nan_value = target_columns.dropna()
    drop_nan_value.to_csv(''+tag_column.split(" ")[0].lower()+'.csv', index=False, header=True, mode='a')
    csv_input = pd.read_csv(''+tag_column.split(" ")[0].lower()+'.csv')
    csv_input['operation'] = tag_column.split(" ")[0].lower()
    csv_input.to_csv(''+tag_column.split(" ")[0].lower()+'.csv', index=False)
  # Create the csv file
  updated_tags_csv_header = ['Scope', 'Operations', 'Input Tags', 'Current Tags or Status Response', 'Status Response']
  with open('updated_tag_details.csv', mode='w', newline='') as updated_tags_header:
    csvwriter = csv.writer(updated_tags_header, delimiter=',')
    csvwriter.writerow(updated_tags_csv_header)
  # Hit the API
  api_files = ("replace", "merge", "delete")
  for tag_file in api_files:
    with open(''+tag_file+'.csv', mode='r', newline='') as tagreader:
      csvreader = csv.reader(tagreader, delimiter=',')
      next(tagreader)
      for row in csvreader:
        target_scope = row[0]
        changed_tags = row[1]
        operation = row[2]
        json_value = {"operation": operation, "properties": {"tags": changed_tags}}
        json_value["properties"]["tags"] = ast.literal_eval(json_value["properties"]["tags"])
        print('Updating - '+target_scope+'\nTags as - '+changed_tags+'\nWith operation - '+operation+'')
        update_tags_request = requests.patch(url = ""+main_url+""+target_scope+"/providers/Microsoft.Resources/tags/default?api-version=2021-04-01", headers = token_header, data = json.dumps(json_value))
        update_tags_response_to_json = update_tags_request.json()
        update_tags_status_response = update_tags_request.status_code
        print('Response - ', update_tags_response_to_json)
        if update_tags_status_response == 200:
          if 'tags' in update_tags_response_to_json['properties']:
            current_tags = update_tags_response_to_json['properties']['tags']
            updated_tags_csv_details = [target_scope, operation, changed_tags, json.dumps(current_tags, indent = 2), update_tags_status_response]
            print('\n\n\n')
          else:
            current_tags = "Tags Not Returned from Azure Rest API for this resource."
            updated_tags_csv_details = [target_scope, operation, changed_tags, current_tags, update_tags_status_response]
            print('\n\n\n')
        else:
          error_message = update_tags_response_to_json['error']['message']
          updated_tags_csv_details = [target_scope, operation, changed_tags, error_message, update_tags_status_response]
          print('\n\n\n')
        with open('updated_tag_details.csv', mode='a', newline='') as updated_tags_details:
          csvwriter = csv.writer(updated_tags_details, delimiter=',')
          csvwriter.writerow(updated_tags_csv_details)
        time.sleep(1)
  
  # Update the excel file for audit data
  audit_csv_data = pd.read_csv('updated_tag_details.csv')
  audit_csv_writer = pd.ExcelWriter('tags.xlsx', engine='openpyxl', mode='a', if_sheet_exists='overlay')
  audit_csv_data.to_excel(audit_csv_writer, sheet_name='Audit-'+todays_date+'', index=False, header=True, startrow=0)
  audit_csv_writer.save()

  audit_workbook = load_workbook(filename = 'tags.xlsx')
  audit_worksheet = audit_workbook['Audit-'+scope+'-'+todays_date+'']
  audit_worksheet.auto_filter.ref = audit_worksheet.dimensions
  audit_workbook.save('tags.xlsx')
  audit_workbook.close()
