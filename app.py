from flask import Flask, render_template, jsonify
from screener import run_scanner

app = Flask(__name__)

@app.route('/')
def index():
    """Serves the main frontend page."""
    return render_template('index.html')

@app.route('/api/scan', methods=['GET'])
def scan_custom_endpoint():
    """API endpoint to run screener and return results.
    We return the Genuine Alpha JSON array directly.
    """
    try:
        # Menjalankan fungsi scanner yang sudah kita wrapper di screener.py
        data = run_scanner()
        
        # Kembalikan sebagai format JSON
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Jalankan server
    app.run(debug=True, port=5000)
