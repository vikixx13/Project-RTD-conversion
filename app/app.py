# app.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, send_file
from werkzeug.utils import secure_filename
from modules import data_processing  # Import your module for data processing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'your_secret_key'  # Set a secret key for Flask-WTF CSRF protection

# Import your functions for data processing
from modules.data_processing import allowed_file, read_resistances, write_temperatures, calculate_errors
from modules.data_processing import newton_raphson_method, polynomial_fit_method

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        method = request.form['method']
        print(f"Method selected: {method}")

        if method in ['newton_raphson', 'poly_fit']:
            if 'files[]' not in request.files:
                flash("No files part in request", 'error')
                return redirect(request.url)
            files = request.files.getlist('files[]')
            print(f"Files uploaded: {[file.filename for file in files]}")
            if len(files) > 3:
                flash("Error: You can upload a maximum of 3 files.", 'error')
                return redirect(request.url)

            delimiter = request.form['delimiter']
            filenames = []
            for file in files:
                if file.filename == '':
                    continue
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    filenames.append(filename)
                else:
                    flash(f"Error: Invalid file format for {file.filename}. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}", 'error')

            results = []
            for filename in filenames:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resistances, measured_temperatures = read_resistances(filepath, delimiter)
                print(f"File {filename} read: {len(resistances)} resistances")
                if method == 'newton_raphson':
                    calculated_temperatures = [newton_raphson_method(R) for R in resistances]
                elif method == 'poly_fit':
                    calculated_temperatures = [polynomial_fit_method(R, resistances, measured_temperatures) for R in resistances]
                errors = calculate_errors(measured_temperatures, calculated_temperatures)

                output_file = os.path.join(app.config['UPLOAD_FOLDER'], f'output_{filename}')
                write_temperatures(resistances, measured_temperatures, calculated_temperatures, errors, output_file)
                results.append(f'output_{filename}')
                print(f"Output file generated: {output_file}")

            return render_template('result.html', filenames=results)

        elif method == 'single_value_conversion':
            try:
                R_t = float(request.form['resistance_value'])
                calculated_temperature = newton_raphson_method(R_t)
                return render_template('single_value_result.html', resistance=R_t, temperature=calculated_temperature)
            except Exception as e:
                print(f"Error in single value conversion: {e}")
                flash(f"Error in single value conversion: {e}", 'error')
                return redirect(request.url)

    return render_template('index.html')

def plot_error_vs_temperature(resistances, measured_temperatures, calculated_temperatures, errors):
    plt.figure(figsize=(8, 6))
    plt.scatter(measured_temperatures, errors, color='blue', label='Error')
    plt.xlabel('Measured Temperature (°C)')
    plt.ylabel('Error (°C)')
    plt.title('Error vs Measured Temperature')
    plt.grid(True)
    plt.legend()
    
    # Convert plot to base64 for embedding in HTML
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.read()).decode()
    plt.close()

    return plot_data

@app.route('/plot/<filename>')
def plot(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    resistances, measured_temperatures = read_resistances(filepath, ',')  # Adjust delimiter as needed
    calculated_temperatures = [newton_raphson_method(R) for R in resistances]  # Example calculation
    errors = calculate_errors(measured_temperatures, calculated_temperatures)
    
    plot_data = plot_error_vs_temperature(resistances, measured_temperatures, calculated_temperatures, errors)
    
    return render_template('plot.html', plot_data=plot_data, filename=filename)

@app.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)


@app.route('/convert_to_excel/<filename>')
def convert_to_excel(filename):
    txt_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    excel_file_path = os.path.splitext(txt_file_path)[0] + '.xlsx'

    try:
        df = pd.read_csv(txt_file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(txt_file_path, encoding='latin1')
    df.to_excel(excel_file_path, index=False, engine='openpyxl')

    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(excel_file_path), as_attachment=True)

@app.route('/concatenate_and_convert_to_excel', methods=['POST'])
def concatenate_and_convert_to_excel():
    files_to_concatenate = request.form.getlist('files_to_concatenate[]')
    combined_data = []

    for filename in files_to_concatenate:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'r') as file:
            combined_data.extend(file.readlines())

    combined_filename = 'combined_output.txt'
    combined_filepath = os.path.join(app.config['UPLOAD_FOLDER'], combined_filename)

    with open(combined_filepath, 'w') as combined_file:
        combined_file.writelines(combined_data)

    excel_filename = 'combined_output.xlsx'
    excel_filepath = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)

    try:
        df = pd.DataFrame(combined_data)
        df.to_excel(excel_filepath, index=False, header=False, engine='openpyxl')

        return send_file(excel_filepath, as_attachment=True)  # Sending the Excel file to the client
    except Exception as e:
        print(f"Error converting to Excel: {e}")
        return f"Error converting to Excel: {e}"
    

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

