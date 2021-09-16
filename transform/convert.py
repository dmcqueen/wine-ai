#!/usr/bin/env python3

import csv
import json
import sys
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

input_files = sys.argv[1]
duplicates = {}

def make_json(input_file):
	
	output_file = input_file[:-4] + ".json"
	data = []
	
	# Open a csv reader called DictReader
	with open(input_file,"r") as csvf:
		csvReader = csv.DictReader(csvf)
		
		# Convert each row into a dictionary
		# and add it to data
		for row in csvReader:

			desc_128 = " ".join(row['description'].split(' ')[:128])

			key = hash(desc_128)
			if duplicates.get(key) != None:
				continue
			else:
				duplicates[key] = True			

			row['desc_vector'] = { "values" : model.encode(desc_128).tolist()}
			row['price'] = float(row['price']) if len(row['price']) > 0 else 0 
			row['points'] = int(row['points']) if len(row['points']) > 0 else 0 
			put = "id:wine:wine::" + row['id']	
			rec = { "put": put ,"fields": row }
			data.append(rec)

	with open(output_file, 'w') as jsonf:
		jsonf.write(json.dumps(data, indent=4))

if __name__ == '__main__':
	for file in input_files.split(' '):
		make_json(file)

