from flask import Flask, render_template, jsonify, request
from screener import run_scanner
from node1_wyckoff import main_node1
from node2_onchain import main_node2
from node3_sentiment import main_node3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, TimeoutError

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

@app.route('/api/onchain', methods=['POST'])
def onchain_endpoint():
    """API endpoint to run Node 2 On-Chain analysis on VCP validated coins."""
    try:
        body = request.get_json()
        passed_vcp_coins = body.get('coins', [])
        
        if not passed_vcp_coins:
            return jsonify({
                'status': 'error',
                'message': 'No VCP validated coins provided.'
            }), 400
            
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(main_node2, passed_vcp_coins)
            try:
                result_df = future.result(timeout=60)
            except TimeoutError:
                return jsonify({
                    'status': 'error',
                    'message': 'Node 2 analysis timed out after 60 seconds. Please try again later.'
                }), 504
        
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

@app.route('/api/sentiment', methods=['POST'])
def sentiment_endpoint():
    """API endpoint to run Node 3 Sentiment analysis on On-Chain validated coins."""
    try:
        body = request.get_json()
        passed_onchain_coins = body.get('coins', [])
        
        if not passed_onchain_coins:
            return jsonify({
                'status': 'error',
                'message': 'No On-Chain validated coins provided.'
            }), 400
            
        result_df = main_node3(passed_onchain_coins)
        
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
