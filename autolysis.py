# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests",
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "numpy",
# ]
# ///
import random
import numpy as np
import pandas as pd
import requests
import sys
import os
import json
import traceback
import io
data = dict()

filename = sys.argv[1]
folder  = '.'.join(filename.split('.')[0:-1])

os.makedirs(name=folder,exist_ok=True)
df = pd.read_csv(filename,encoding_errors='ignore')
column_name = random.choice(df.describe().columns)

data['statistics'] = json.loads((df.describe().to_json()))[column_name]

data['column name'] = column_name


# print(data)
# content = (
#     "consider the column name and statistics provided of the column data"
#     "only respond True if binnable and False if not binnable and also specify reason"
# )


# {"is_binnable":True/False, "reason":"why it's binnable"}
# functions = [
#     {
#         "name":"binnable",
#         "description":"Identify if the column is binnable or not also give reason",
#         "parameters":{
#             "type":"object",
#             "properties":{
#                 "is_binnable":{
#                     "type":"boolean",
#                     "description":"it is a boolean that represents if column is binnable or not"
#                 },
#                 "reason":{
#                     "type":"string",
#                     "description":"give reason why you think it's binnable or not binnable"
#                 }
#             },
#             "required":['is_binnable','reason']

#         }
#     }
# ]

AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AIPROXY_TOKEN}"}
url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
# json_data = {
#     "model":"gpt-4o-mini",
#     "messages":[
#         {
#             "role":"system",
#             "content":content
#         },
#         {
#             "role":"user",
#             "content":json.dumps(data)
#         },
        
#     ],
#     "functions": functions,
#     "function_call":{"name":"binnable"}
# }

# r = requests.post(url=url, headers=headers,json=json_data)
## to_uncommented
instruction =  (
                "do not make your own data, dataset is stored in the dataframe named ```df```"
                "do not add comments to the code"    
                "generate only python code ."
                "create an appropriate chart using seaborn library for the column data."
                "Use the column data statistics provided to get the column name and generate code for appropriate chart."
                "export the chart as png."
                )



## to_uncommented
functions = [
    {
        "name":"generate_chart",
        "description": "Generate python code without comments to create a chart based on the prompt, export it as a png file and provide the name of the png file and also send names of modules that were used",
        "parameters": {
            "type":"object",
            "required":['python_code','chart_name','dependencies'],
            "properties":{
                "python_code":{
                    "type":"string",
                    "description":"Generate python code without comments that creates appropriate chart"
                },
                "chart_name":{
                    "type":"string",
                    "description":"chart/file name of png chart"
                },
                "dependencies":{
                    "type":"string",
                    "description":"Give comma seperated names of the modules that were used in this script"
                }
            }   
        }
    }
]

## to_uncommented
json_data = {
    "model":"gpt-4o-mini",
    "messages":[
        {
            "role":"system",
            "content":instruction
        },
        {
            "role":"user",
            "content":json.dumps(data)
        },
        
    ],
    "functions":functions,
    "function_call":{"name":"generate_chart"}
}



def resend_request(code, error):
    data1 = code + "\n" + error
    json_data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system", 
                    "content": instruction
                },
                {
                    "role": "user", 
                    "content": data1
                }
            ],
            "functions": functions,
            "function_call": {"name": "generate_chart"} 
        }
    r = requests.post(url=url, headers=headers, json=json_data)
    return r 

## to_uncommented
limit = 0
flag = True
r = requests.post(url=url, headers=headers, json=json_data)
code_list = []
error_list = []

while flag and limit < 3:
    try : 
        if limit >= 1 :
            r = resend_request(code=code,error=error)
        code = json.loads(r.json()['choices'][0]['message']['function_call']['arguments'])['python_code'] 
        code_list.append(code)
        exec(code)
        flag = False
    except Exception as e : 
        buffer = io.StringIO()
        traceback.print_exc(file=buffer)
        traceback_output = buffer.getvalue()
        # print("############")
        # print(traceback_output)
        error = '\n'.join(traceback_output.split('\n')[3:])
        
        error_list.append(error)
        # print(error)
        buffer.close()
    finally : 
        limit += 1

chart_name = json.loads(r.json()['choices'][0]['message']['function_call']['arguments'])['chart_name']
# image_path = 'original_publication_year_distribution.png'
src = os.path.join(os.getcwd(),chart_name)
dest = os.path.join(os.getcwd(),folder,chart_name)
# image_path = src

os.rename(src,dest)

import base64

# # Function to encode an image to Base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    

base64_image = encode_image(dest)

json_data = {
    "model":"gpt-4o-mini",
    "messages":[
             {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image?",
                },
                {
                    "type": "image_url",
                    "image_url": {
                    "url":  f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ],
        }
    ]
}

r = requests.post(url=url,headers=headers,json=json_data)

with open(file=f'{folder}/Readme.md',encoding='utf-8',mode='a') as f:
    f.write(r.json()['choices'][0]['message']['content'])
print(r.json())
