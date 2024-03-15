from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import time
import subprocess
import json
import tempfile
from flask import make_response

app = Flask(__name__)

@app.route('/process-image', methods=['POST'])
def process_image():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(tempfile.gettempdir(), filename)
    file.save(input_path)

    output_filename = f'processed_{filename}'
    output_path = os.path.join(tempfile.gettempdir(), output_filename)

    # Process the image
    command = ['python', 'main.py', input_path, output_path]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Image processing failed', 'message': str(e)}), 500
    finally:
        # Clean up input file immediately after processing
        os.remove(input_path)

    # Send the processed file
    try:
        return send_file(
            output_path,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=output_filename
        )
    except Exception as e:
        return jsonify({'error': 'Failed to send processed image', 'message': str(e)}), 500
    finally:
        # Schedule the cleanup of the output file, give some time for it to be sent completely
        import threading
        def cleanup_file(path):
            time.sleep(10)  # Give some time for the file to be sent
            os.remove(path)
        threading.Thread(target=cleanup_file, args=(output_path,)).start()

@app.route('/angle', methods=['GET'])
def get_angle():
    try:
        with open('angle.json', 'r') as f:
            angle = json.load(f)
        return jsonify(angle)
    except Exception as e:
        return jsonify({'error': 'Failed to get angle', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)