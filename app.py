from flask import Flask, render_template, jsonify, request
from screener import run_scanner
from node1_wyckoff import main_node1
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    """Serves the main frontend page."""
    return render_template('index.html')

@app.route('/api/scan', methods=['GET'])
def scan_custom_endpoint():
    """API endpoint to run screener and return results."""
    try:
        data = run_scanner()
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/wyckoff', methods=['POST'])
def wyckoff_endpoint():
    """API endpoint to run Node 1 Wyckoff analysis on a given watchlist."""
    try:
        body = request.get_json()
        symbols = body.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'status': 'error',
                'message': 'No symbols provided.'
            }), 400
        
        result_df = main_node1(symbols)
        
        if result_df is not None and not result_df.empty:
            result_df = result_df.where(pd.notnull(result_df), None)
            return jsonify({
                'status': 'success',
                'data': result_df.to_dict(orient='records')
            })
        else:
            return jsonify({
                'status': 'success',
                'data': []
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
