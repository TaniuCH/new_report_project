from flask import Flask, render_template, send_file, url_for
from html2image import Html2Image
from pyppeteer import launch
import os
import json
import nest_asyncio
import subprocess
import tempfile
from flask import request

app = Flask(__name__)
nest_asyncio.apply()

def get_translations_dict(lang):
    """Fetch translations based on the language."""
    path = os.path.join(os.getcwd(), 'translation.json')
    if not os.path.isfile(path):
        return {}
    with open(path) as f:
        translations = json.load(f)
        return translations.get(lang, {})

# Load translations
translations = get_translations_dict('en')
@app.route('/')

def index():
    """Render index.html with translations for English."""
    
    # Load the CSS content
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    return render_template('index.html', style_sheet_content=style_sheet_content, **translations)



def get_score_card_variables(results, module_risk, module_density, module_quality, module_diagnostics):
    """Return scorecard variables."""
        
    # Extract details from the results
    higher_density = results.get('overall_density', '')  
    overall_risk = results.get('overall_risk', '')  
    lower_quality = results.get('lower_quality', '') 
    higher_diagnostics = results.get('higher_diagnostics', '') 
    patient_age = results.get('patient_age', '')

    # Set the corresponding classes for risk, density, quality, and diagnostics
    risk_class = {
        'normal': 'risk-normal',
        'increased': 'risk-increased',
        'high': 'risk-high'
    }.get(overall_risk, 'risk-none')

    density_class = {
        'A': 'density-A',
        'B': 'density-B',
        'C': 'density-C',
        'D': 'density-D'
    }.get(higher_density, 'density-none')

    quality_class = {
        'perfect': 'quality-perfect',
        'good': 'quality-good',
        'moderate': 'quality-moderate',
        'insufficient': 'quality-insufficient'
    }.get(lower_quality, 'quality-none')

    diagnostic_class = {
        "2": 'diagnostics-2',
        "3": 'diagnostics-3',
        "4": 'diagnostics-4',
        "5": 'diagnostics-5'
    }.get(higher_diagnostics, 'diagnostics-none')

    # Prepare the variables to return
    variables = {
        'report_title': "Score Card",
        'patient_age': patient_age,
        'module_risk': "show" if module_risk else "hide",
        'risk_class': risk_class,
        'overall_risk': overall_risk,
        'module_density': "show" if module_density else "hide",
        'density_class': density_class,
        'higher_density': higher_density,
        'module_quality': "show" if module_quality else "hide",
        'quality_class': quality_class,
        'lower_quality': lower_quality,
        'module_diagnostics': "show" if module_diagnostics else "hide",
        'diagnostic_class': diagnostic_class,
        'higher_diagnostics': higher_diagnostics
    }
    
    return {**translations, **variables}

@app.route('/score-card')
def report():
    """Render the scorecard with necessary variables."""

    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    with open('results.json') as f:
        results = json.load(f)
    
    # Module flags (True or False based on data availability)
    module_risk = True
    module_density = True
    module_quality = True
    module_diagnostics = True
    
    variables = get_score_card_variables(results, module_risk, module_density, module_quality, module_diagnostics)
    
    return render_template('score_card.html', style_sheet_content=style_sheet_content, **variables)

@app.route('/pyppeteer-scorecard')
def generate_image_pyppeteer():
    """Generate an image from rendered HTML for the scorecard report using Pyppeteer."""
    report_type = request.args.get('report_type', 'scorecard')
    
    # Set template and output file name based on report type
    template_name = 'score_card.html'  # Use score_card.html for generating the image
    output_file_name = 'scorecard_report_image_pyppeteer.png'

    with open('results.json') as f:
        results = json.load(f)

    # Module flags (True or False based on data availability)
    module_risk = True
    module_density = True
    module_quality = True
    module_diagnostics = True
    
    variables = get_score_card_variables(results, module_risk, module_density, module_quality, module_diagnostics)

    return generate_image_with_pyppeteer(template_name, output_file_name, variables)


def generate_image_with_pyppeteer(template_name, output_file_name, variables):
    """Generate an image from HTML using Pyppeteer with the specified template and variables."""
    
    # Ensure you're loading the correct CSS content for styling
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    # Render the HTML string with variables
    html_string = render_template(template_name, style_sheet_content=style_sheet_content, **variables)

    # Write the rendered HTML to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html_file:
        temp_html_file.write(html_string.encode('utf-8'))
        temp_html_path = os.path.abspath(temp_html_file.name)

    # Use Pyppeteer to generate the image
    try:
        result = subprocess.run(
            ['python', 'pyppeteer_capture.py', temp_html_path, output_file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e.stderr.decode()}", 500

    return send_file(output_file_name, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5001)



