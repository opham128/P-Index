from flask import Flask, request, jsonify
from framework.researcher import find_researcher_ids, get_papers_by_researcher_id
from framework.pindex import compute_pindex
import pandas as pd
import numpy as np

import os
from flask import Flask, request, jsonify, send_from_directory

# Configure Flask to serve static files from the public folder
app = Flask(__name__, static_folder='../public', static_url_path='/')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    
    if not first_name or not last_name:
        return jsonify({'error': 'First and last name required'}), 400
        
    df, counter = find_researcher_ids(first_name, last_name)
    
    if df.empty:
        return jsonify({'researchers': []})
        
    profiles = []
    for rid, group in df.groupby('researcher_id'):
        if pd.isna(rid) or not rid:
            continue
        display_name = group.iloc[0]['display_name']
        count = counter.get(rid, 0)
        profiles.append({
            'researcher_id': rid,
            'display_name': display_name,
            'count': count
        })
        
    profiles.sort(key=lambda x: x['count'], reverse=True)
        
    return jsonify({'researchers': profiles})

@app.route('/api/papers', methods=['POST'])
def papers():
    data = request.json
    researcher_id = data.get('researcher_id')
    
    if not researcher_id:
        return jsonify({'error': 'researcher_id required'}), 400
        
    df = get_papers_by_researcher_id(researcher_id)
    
    if df.empty:
        return jsonify({'papers': []})
        
    # Replace NaN with empty string to avoid JSON errors
    df = df.replace({np.nan: ''})
    papers_list = df.to_dict('records')
    
    return jsonify({'papers': papers_list})

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    papers_list = data.get('papers', [])
    
    if not papers_list:
        return jsonify({'error': 'No papers provided'}), 400
        
    df = pd.DataFrame(papers_list)
    
    out_df, pindex_score = compute_pindex(df)
    
    # Handle NaN in pindex_score
    if pd.isna(pindex_score):
        pindex_score = None
        
    return jsonify({'pindex': pindex_score})
