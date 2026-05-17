import sys
import os
from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
import json

# Add the current directory to sys.path so framework can be imported
sys.path.append(os.path.dirname(__file__))

from framework.researcher import find_researcher_ids, get_papers_by_researcher_id
from framework.pindex import compute_pindex

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
    org = data.get('org', '')
    
    if not first_name or not last_name:
        return jsonify({'error': 'First and last name required'}), 400
        
    try:
        df, counter = find_researcher_ids(first_name, last_name, org=org or None)
    except Exception as e:
        if "WOS_RATE_LIMIT" in str(e):
            return jsonify({'error': 'web_of_science_rate_limit'}), 429
        return jsonify({'error': str(e)}), 500
    
    if df.empty:
        return jsonify({'researchers': []})
        
    from framework.api import wos_search
    profiles = []
    for rid, group in df.groupby('researcher_id'):
        if pd.isna(rid) or not rid:
            continue
        display_name = group.iloc[0]['display_name']
        
        try:
            res = wos_search(f'AI=("{rid}")', limit=1)
            count = res.get('metadata', {}).get('total', 0)
        except Exception:
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
        
    try:
        df = get_papers_by_researcher_id(researcher_id)
    except Exception as e:
        if "WOS_RATE_LIMIT" in str(e):
            return jsonify({'error': 'web_of_science_rate_limit'}), 429
        return jsonify({'error': str(e)}), 500
    
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
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    if not papers_list:
        return jsonify({'error': 'No papers provided'}), 400
        
    df = pd.DataFrame(papers_list)
    
    try:
        out_df, pindex_score, pindex_weighted, total_docs = compute_pindex(df, first_name, last_name)
    except Exception as e:
        if "WOS_RATE_LIMIT" in str(e):
            return jsonify({'error': 'web_of_science_rate_limit'}), 429
        return jsonify({'error': str(e)}), 500
    
    # Handle NaN in pindex_score
    if pd.isna(pindex_score):
        pindex_score = None
    if pd.isna(pindex_weighted):
        pindex_weighted = None
 
    # Serialize per-paper ranked results
    # Use to_json -> loads to correctly handle numpy types (int64, float64) and NaN -> null
    ranked_cols = [
        'title', 'journal', 'year', 'times_cited', 'pr', 'cell_size', 
        'document_types', 'weight', 'pr_weighted', 'author_rank', 'num_authors'
    ]
    cols_to_use = [c for c in ranked_cols if c in out_df.columns]
    ranked_df = out_df[cols_to_use].copy()
    ranked_papers = json.loads(ranked_df.to_json(orient='records'))
        
    return jsonify({
        'pindex': pindex_score, 
        'pindex_weighted': pindex_weighted,
        'total_docs': total_docs, 
        'ranked_papers': ranked_papers
    })
