from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import json
import pyshark

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Configure upload and converted folders
UPLOAD_FOLDER = './uploads'
CONVERTED_FOLDER = './converted_json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# Ensure the folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    username = request.form['username']
    file = request.files['file']

    if file and file.filename.endswith('.pcap'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Convert PCAP to JSON
        json_filename = f"{username}_{file.filename.replace('.pcap', '.json')}"
        json_filepath = os.path.join(app.config['CONVERTED_FOLDER'], json_filename)

        try:
            # Convert file synchronously on the main thread
            convert_pcap_to_json(file_path, json_filepath)
            flash('File uploaded and converted successfully', 'success')
        except Exception as e:
            flash(f'Error during conversion: {e}', 'error')
            return redirect(url_for('upload_form'))

        session['success_message'] = 'File uploaded and converted successfully'
        session['selected_file'] = json_filename
        return redirect(url_for('view_files'))

    flash('Invalid file type, only .pcap files are allowed', 'error')
    return redirect(url_for('upload_form'))

@app.route('/view_files', methods=['GET', 'POST'])
def view_files():
    converted_files = [
        file for file in os.listdir(app.config['CONVERTED_FOLDER']) if file.endswith('.json')
    ]

    if request.method == 'POST':
        selected_file = request.form.get('selected_file')
        session['selected_file'] = selected_file
        return redirect(url_for('search_results', filename=selected_file))

    return render_template('view_files.html', files=converted_files)

@app.route('/search_results/<filename>')
def search_results(filename):
    file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)

    if not os.path.exists(file_path):
        flash('File not found!', 'error')
        return redirect(url_for('view_files'))

    with open(file_path) as f:
        file_data = json.load(f)

    return render_template('search_results.html', filename=filename, json_data=file_data)

@app.route('/api/search_keys', methods=['GET'])
def search_keys():
    query = request.args.get('q', '').lower()
    filename = session.get('selected_file')
    file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)

    if not os.path.exists(file_path):
        return jsonify([])

    with open(file_path) as f:
        file_data = json.load(f)

    suggestions = search_json(file_data, query)
    return jsonify(suggestions)

@app.route('/api/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('q', '').lower()
    files = [file for file in os.listdir(app.config['CONVERTED_FOLDER']) if file.endswith('.json')]

    suggestions = []
    for file in files:
        if query in file.lower():
            suggestions.append({"filename": file})

    return jsonify(suggestions)

def search_json(data, query):
    matches = []
    if isinstance(data, dict):
        for key, value in data.items():
            if query in key.lower():
                matches.append({"key": key, "value": value})
            if isinstance(value, (dict, list)):
                matches.extend(search_json(value, query))
    elif isinstance(data, list):
        for item in data:
            matches.extend(search_json(item, query))
    return matches

def convert_pcap_to_json(input_pcap_path, output_json_path):
    """Convert a PCAP file to a JSON file using PyShark."""
    packets = pyshark.FileCapture(input_pcap_path)
    data = []

    # Extract packet details
    for packet in packets:
        packet_dict = {}
        for layer in packet.layers:
            packet_dict[layer.layer_name] = layer._all_fields
        data.append(packet_dict)

    with open(output_json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    packets.close()

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



# Initialize an empty list in session to store key-value pairs
@app.before_request
def initialize_session():
    if 'validated_pairs' not in session:
        session['validated_pairs'] = []

@app.route('/validate', methods=['GET'])
def validate():
    key = request.args.get('key')
    value = request.args.get('value')
    return render_template('Validate.html', key=key, value=value)

# @app.route('/validate', methods=['POST'])
# def validate():
#     template_name = request.form.get('template_name')
#     selected_pairs = request.form.get('selected_pairs')

#     if template_name and selected_pairs:
#         session['template_name'] = template_name
#         session['validated_pairs'] = json.loads(selected_pairs)
#         flash('Template name and selected pairs saved successfully!', 'success')
#     else:
#         flash('Template name and selected pairs are required!', 'error')

#     return redirect(url_for('template_structure'))






@app.route('/delete', methods=['POST'])
def delete_entry():
    if 'selected_pairs' in session:
        selected_pairs = session['selected_pairs']
        index = int(request.form.get('index')) - 1  # Convert index to 0-based
        if 0 <= index < len(selected_pairs):
            del selected_pairs[index]
            session['selected_pairs'] = selected_pairs  # Save back to session
            flash('Pair deleted successfully!', 'success')
        else:
            flash('Invalid index!', 'error')

    # Debugging: Print session data
    print("Session data after delete:", session.get('selected_pairs'))

    return redirect(url_for('validate'))

@app.route('/template_structure', methods=['GET', 'POST'])
def template_structure():
    templates_folder = './templates_storage'
    os.makedirs(templates_folder, exist_ok=True)

    if request.method == 'POST':
        template_name = session.get('template_name', 'Unnamed Template')
        validated_pairs = session.get('validated_pairs', [])

        if not validated_pairs:
            flash('No validated pairs found!', 'error')
            return redirect(url_for('template_structure'))

        # Save the template data
        template_data = {'name': template_name, 'data': validated_pairs}
        template_path = os.path.join(templates_folder, f'{template_name}.json')

        try:
            with open(template_path, 'w') as f:
                json.dump(template_data, f, indent=4)
            flash('Template saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving template: {e}', 'error')

    # Load templates for display
    templates = []
    for file_name in os.listdir(templates_folder):
        if file_name.endswith('.json'):
            with open(os.path.join(templates_folder, file_name)) as f:
                templates.append(json.load(f))

    return render_template('template_structure.html', templates=templates)





if __name__ == '__main__':
    app.run(debug=True)
