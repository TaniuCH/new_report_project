from flask import Flask, render_template, send_file, url_for
from html2image import Html2Image
from pyppeteer import launch
from selenium import webdriver
from weasyprint import HTML
from spire.doc import Document, FileFormat, XHTMLValidationType, ImageType
import os
import json
import nest_asyncio
import asyncio
import subprocess
from PIL import Image
import cairosvg
from selenium.webdriver.chrome.service import Service
import tempfile
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import request


app = Flask(__name__)
nest_asyncio.apply()

def get_translations_dict(lang):
    """Fetch translations based on the language."""
    path = os.path.join(os.getcwd(), 'translation.json')
    if not os.path.isfile(path):
        print('Translations not found.')
        return {}
    with open(path) as f:
        translations = json.load(f)
        return translations.get(lang, {})
    
@app.route('/')

def index():
    """Render index.html with translations for English."""
    translations = get_translations_dict('en')

    # Load the CSS content
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    return render_template('index.html', style_sheet_content=style_sheet_content, **translations)


def get_report_variables():
    """Return common variables including images for report rendering."""
    # Get the absolute URL for static image resources
    base_url = request.url_root  # get the base URL

    # Absolute URLs for images
    rcc_proj_img = base_url + url_for('static', filename='images/rcc.png')  
    lcc_proj_img = base_url + url_for('static', filename='images/lcc.png')  
    rmlo_proj_img = base_url + url_for('static', filename='images/rmlo.png')  
    lmlo_proj_img = base_url + url_for('static', filename='images/lmlo.png')  

    translations = get_translations_dict('en')
    with open('results.json') as f:
        results = json.load(f)
    opacities_rcc = results.get('opacities', {}).get('bbox', {}).get('rcc', {})
    opacities_lcc = results.get('opacities', {}).get('bbox', {}).get('lcc', {})
    opacities_rmlo = results.get('opacities', {}).get('bbox', {}).get('rmlo', {})
    opacities_lmlo = results.get('opacities', {}).get('bbox', {}).get('lmlo', {})
    lesion_types = ['birads2', 'birads3', 'birads4', 'birads5', 'lesionKnown']
    rectangles_rcc = get_lesion_shapes(opacities_rcc, lesion_types)
    rectangles_lcc = get_lesion_shapes(opacities_lcc, lesion_types)
    rectangles_rmlo = get_lesion_shapes(opacities_rmlo, lesion_types)
    rectangles_lmlo = get_lesion_shapes(opacities_lmlo, lesion_types)

    variables = {
        "rcc_proj_img" : rcc_proj_img,
        "lcc_proj_img" : lcc_proj_img,
        "rmlo_proj_img" : rmlo_proj_img,
        "lmlo_proj_img" : lmlo_proj_img,
        'breast_image_alt': "Breast Projection Image",
        'report_title': "Mammography Report",
        'rectangles_rcc' : rectangles_rcc,
        "rectangles_lcc": rectangles_lcc,
        "rectangles_rmlo" : rectangles_rmlo,
        "rectangles_lmlo" : rectangles_lmlo
    }

    return {**translations, **variables}

def get_lesion_div(box, color, border_radius, birads, score, font_size, border_style, label_mapping):
    """
    Generate a div for a lesion based on its bounding box and properties.
    """
    top, left, width, height = box

    div = f'''
    <div style="
        position: absolute;
        top: {top * 100}%;
        left: {left * 100}%;
        width: {width * 100}%;
        height: {height * 100}%;
        border: 2px {border_style} {color};
        border-radius: {border_radius};
        font-size: {font_size};
        color: {color};
        z-index:{200}
    ">
        {label_mapping.get(birads)}
    </div>
    '''
    return div

def get_lesion_shapes(opacities, birads_list_opac):
    """
    Extracts the lesion shapes for the given opacities (projections) and BI-RADS categories.
    Returns a single string with all the divs.
    """
    lesion_shapes = []

    # Iterate through each projection (e.g., lmlo, lcc, rmlo, rcc)
    for projection, projection_lesions in opacities.items():
        print(f"Processing projection: {projection}")

        # Check if projection_lesions is a dictionary (expected structure)
        if isinstance(projection_lesions, dict):
            for birads_type in birads_list_opac:
                lesion_list = projection_lesions.get(birads_type)
                if isinstance(lesion_list, list) and lesion_list:
                    print(f"Found lesions for {birads_type}: {lesion_list}")
                    # Append the divs to the lesion_shapes list
                    lesion_shapes.append(_get_lesion_shapes(lesion_list, birads_type))
                else:
                    print(f"No lesions found for {birads_type}.")
        elif isinstance(projection_lesions, list):  # If projection_lesions is a list
            # Process all lesions as a list
            print(f"Unexpected structure for projection lesions: {projection_lesions}")
            lesion_shapes.append(_get_lesion_shapes(projection_lesions, 'lesion'))

    # Join all the divs into a single string
    return ''.join(lesion_shapes)

def _get_lesion_shapes(lesion_list, birads_type):
    if not lesion_list:
        return ''

    print(f"DIV: {birads_type}")  # Debugging
    # Define colors for the BI-RADS and other lesion types
    colors = {
        'birads2': 'green',
        'birads3': 'orange',
        'birads4': '#f14b16',
        'birads5': 'red',
        'lesionKnown': 'cyan'
    }

    shapes = ''  

    border_radius = 'inherit'  
    border_style = 'solid'  
    font_size = '10px'

    # Define label mapping for the lesions (making sure to handle BI-RADS labels)
    label_mapping = {
        'birads2': 'BI-RADS_2',
        'birads3': 'BI-RADS_3',
        'birads4': 'BI-RADS_4',
        'birads5': 'BI-RADS_5',
        'lesionKnown': 'Known'
    }

    print(f"START LOOP: {lesion_list}")  # Debugging

    # Loop through the lesions in the lesion list
    for lesion in lesion_list:
        print(f"Processing lesion: {lesion}")  # Debugging
        box = lesion.get('box')
        if not box:
            print(f"No box found for lesion {lesion}")
            continue

        # Generate the div for this lesion
        shapes += get_lesion_div(
            box, 
            colors.get(birads_type, 'red'), 
            border_radius, 
            label_mapping.get(birads_type, 'Unknown'),  # Use label mapping here
            lesion.get('score'), 
            font_size, 
            border_style, 
            label_mapping
        )

    return shapes

@app.route('/generate-image')
def generate_image():
    with open('results.json') as f:
        results = json.load(f)
    
    # Define the list of BI-RADS categories you're interested in
    birads_list_opac = ['birads2', 'birads3', 'birads4', 'birads5', 'lesionKnown']

    # Extract the lesion shapes for each projection
    opacities_rcc = results.get('opacities', {}).get('bbox', {}).get('rcc', {})
    rectangles_rcc = get_lesion_shapes(opacities_rcc, birads_list_opac)
    # Pass lesion shapes to the template as needed
    variables = get_report_variables()
    variables['rectangles_rcc'] = rectangles_rcc

    return render_template('report_quality.html', **variables)


# HTML2Image Route
@app.route('/html-2-img-html-to-image')
def generate_image_html2image():
    """Generate an image using HTML2Image."""
    
    # Load the CSS content from the external file
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    # Get variables needed for rendering
    variables = get_report_variables()

    # Embed the CSS directly into the HTML string
    html_string = render_template('report_quality.html', style_sheet_content=style_sheet_content, **variables)

    # Create an Html2Image instance
    hti = Html2Image()
    hti.output_path = os.getcwd()

    # Generate the image
    hti.screenshot(html_str=html_string, save_as='quality_report_image_html2image.png', size=(1280, 2000))

    return send_file('quality_report_image_html2image.png', as_attachment=True)


# Spire Route
@app.route('/spire-html-to-image')
def generate_image_spire():
    """Convert HTML to Image using Spire.Doc."""
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    html_string = render_template('report_quality.html', style_sheet_content=style_sheet_content)
    html_file_path = os.path.join(os.getcwd(), 'templates', 'report_quality.html')
    document = Document()
    document.LoadFromFile(html_file_path, FileFormat.Html, XHTMLValidationType.none)
    imageStream = document.SaveImageToStreams(0, ImageType.Bitmap)
    output_dir = os.path.join(os.getcwd(), 'output')
    os.makedirs(output_dir, exist_ok=True)
    image_file_path = os.path.join(output_dir, 'HtmlToImage_Spire.png')
    with open(image_file_path, 'wb') as imageFile:
        imageFile.write(imageStream.ToArray())
    document.Close()
    return send_file(image_file_path, as_attachment=True)


# Pyppeteer Route
@app.route('/pyppeteer-html-to-image')
def generate_image_pyppeteer():
    """Generate an image from rendered HTML using Pyppeteer."""
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    variables = get_report_variables()

    html_string = render_template('report_quality.html', style_sheet_content=style_sheet_content, **variables)

    with open('debug_rendered_report_quality.html', 'w') as debug_file:
        debug_file.write(html_string)

    output_path = os.path.abspath('quality_report_image_pyppeteer.png')

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html_file:
        temp_html_file.write(html_string.encode('utf-8'))
        temp_html_path = os.path.abspath(temp_html_file.name)

    print(f"Temp HTML file path: {temp_html_path}")
    print(f"Output image path: {output_path}")

    try:
        result = subprocess.run(
            ['python', 'pyppeteer_capture.py', temp_html_path, output_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed: {e.stderr.decode()}")
        return f"An error occurred: {e.stderr.decode()}", 500

    return send_file(output_path, as_attachment=True)


# WeasyPrint Route
@app.route('/weasy-html-to-image')
def generate_image_weasyprint():
    """Generate an image from HTML using WeasyPrint and CairoSVG."""
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    html_string = render_template('report_quality.html', style_sheet_content=style_sheet_content)
    svg_output_path = os.path.join(os.getcwd(), 'quality_report_svg_weasyprint.svg')
    png_output_path = os.path.join(os.getcwd(), 'quality_report_image_weasyprint.png')

    HTML(string=html_string).write_pdf(svg_output_path)
    cairosvg.svg2png(url=svg_output_path, write_to=png_output_path)

    return send_file(png_output_path, as_attachment=True)

# Selenium Route
def html_to_image_selenium(html_file_path, output_path):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no visible window)
    options.add_argument('--disable-gpu')

    # Create a service object with ChromeDriverManager
    service = Service(ChromeDriverManager().install())

    # Pass the service object to Chrome
    driver = webdriver.Chrome(service=service, options=options)

    # Load the temporary HTML file
    driver.get(f"file://{html_file_path}")  # Load the HTML file in the browser

    # Wait for the body to be fully loaded
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    driver.execute_script("document.body.style.overflow = 'hidden';")

    total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
    total_height += 100  
    driver.set_window_size(1280, total_height)
    driver.execute_script("window.scrollTo(0, 0);")
    driver.implicitly_wait(1)
    driver.save_screenshot(output_path)
    driver.quit()


@app.route('/selenium-html-to-image')
def generate_image_selenium():
    """Generate an image from rendered HTML using Selenium."""
    
    translations = get_translations_dict('en')  # Assuming 'en' is the language selected

    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    # Render the HTML with dynamic translations and styles
    html_string = render_template('report_quality.html', 
                                  style_sheet_content=style_sheet_content,
                                  **translations)

    output_path = os.path.join(os.getcwd(), 'quality_report_image_selenium.png')

    # Write the HTML to a temporary file for Selenium
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html_file:
        temp_html_file.write(html_string.encode('utf-8'))
        temp_html_path = temp_html_file.name

    # Use Selenium to load the temp HTML file and capture the screenshot
    html_to_image_selenium(temp_html_path, output_path)

    os.remove(temp_html_path)

    return send_file(output_path, as_attachment=True)



@app.route('/report')
def report():
    """Render the report_quality.html with necessary variables."""
    translations = get_translations_dict('en')

    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    variables = get_report_variables()


    return render_template('report_quality.html', style_sheet_content=style_sheet_content, **variables)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
