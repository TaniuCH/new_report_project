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
    
translations = get_translations_dict('en')

@app.route('/')

def index():
    """Render index.html with translations for English."""

    # Load the CSS content
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    return render_template('index.html', style_sheet_content=style_sheet_content, **translations)


def get_report_variables():
    """Return common variables including images and quality shapes for report rendering."""
    base_url = request.url_root

    rcc_proj_img = base_url + url_for('static', filename='images/rcc.png')  
    lcc_proj_img = base_url + url_for('static', filename='images/lcc.png')  
    rmlo_proj_img = base_url + url_for('static', filename='images/rmlo.png')  
    lmlo_proj_img = base_url + url_for('static', filename='images/lmlo.png')  
    # TODO: Obtain image width and height dynamically per projection 
    img_width= 443
    img_height= 545

    with open('results.json') as f:
        results = json.load(f)
    
    # Fetch opacities lesions
    opacities_rcc = results.get('opacities', {}).get('bbox', {}).get('rcc', {})
    opacities_lcc = results.get('opacities', {}).get('bbox', {}).get('lcc', {})
    opacities_rmlo = results.get('opacities', {}).get('bbox', {}).get('rmlo', {})
    opacities_lmlo = results.get('opacities', {}).get('bbox', {}).get('lmlo', {})

    # Fetch microcalc lesions 
    microcalc_rcc = results.get('microcalc', {}).get('bbox', {}).get('rcc', {})
    microcalc_lcc = results.get('microcalc', {}).get('bbox', {}).get('lcc', {})
    microcalc_rmlo = results.get('microcalc', {}).get('bbox', {}).get('rmlo', {})
    microcalc_lmlo = results.get('microcalc', {}).get('bbox', {}).get('lmlo', {})

    # Fetch quality indicators for each projection
    quality_rcc = results.get('quality', {}).get('bbox', {}).get('rcc', {})
    quality_lcc = results.get('quality', {}).get('bbox', {}).get('lcc', {})
    quality_rmlo = results.get('quality', {}).get('bbox', {}).get('rmlo', {})
    quality_lmlo = results.get('quality', {}).get('bbox', {}).get('lmlo', {})

    # **TODO: obtain the ones we need to show from env file 
    opacities_types = ['vessels', 'birads2', 'birads3', 'birads4', 'birads5', ]
    microcalc_types = ['birads2', 'birads3', 'birads4', 'birads5', 'lesionKnown']
    
    # Get lesion shapes for each projection
    opacities_rcc = get_lesion_shapes(opacities_rcc, opacities_types)
    opacities_lcc = get_lesion_shapes(opacities_lcc, opacities_types)
    opacities_rmlo = get_lesion_shapes(opacities_rmlo, opacities_types)
    opacities_lmlo = get_lesion_shapes(opacities_lmlo, opacities_types)

    microcalc_rcc = get_lesion_shapes(microcalc_rcc, microcalc_types, microcalc=True)
    microcalc_lcc = get_lesion_shapes(microcalc_lcc, microcalc_types, microcalc=True)
    microcalc_rmlo = get_lesion_shapes(microcalc_rmlo, microcalc_types, microcalc=True)
    microcalc_lmlo = get_lesion_shapes(microcalc_lmlo, microcalc_types, microcalc=True)

    # Fetch quality shapes (parenchyma, pectoralis, skin folds) for each projection
    parenchyma_rcc = get_quality_shapes(quality_rcc.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_rcc = get_quality_shapes(quality_rcc.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_rcc = get_quality_shapes(quality_rcc.get('skinFolds', []) or [], 'skinFolds', img_width, img_height)

    parenchyma_lcc = get_quality_shapes(quality_lcc.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_lcc = get_quality_shapes(quality_lcc.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_lcc = get_quality_shapes(quality_lcc.get('skinFolds', []) or [], 'skinFolds', img_width, img_height)

    parenchyma_rmlo = get_quality_shapes(quality_rmlo.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_rmlo = get_quality_shapes(quality_rmlo.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_rmlo = get_quality_shapes(quality_rmlo.get('skinFolds', []) or [], 'skinFolds', img_width, img_height)

    parenchyma_lmlo = get_quality_shapes(quality_lmlo.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_lmlo = get_quality_shapes(quality_lmlo.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_lmlo = get_quality_shapes(quality_lmlo.get('skinFolds', []) or [], 'skinFolds', img_width, img_height)

    variables = {
        "rcc_proj_img" : rcc_proj_img,
        "lcc_proj_img" : lcc_proj_img,
        "rmlo_proj_img" : rmlo_proj_img,
        "lmlo_proj_img" : lmlo_proj_img,
        'breast_image_alt': "Breast Projection Image",
        'report_title': "Mammography Report",
        'opacities_rcc' : opacities_rcc,
        "opacities_lcc": opacities_lcc,
        "opacities_rmlo" : opacities_rmlo,
        "opacities_lmlo" : opacities_lmlo,
        'microcalc_rcc' : microcalc_rcc,
        "microcalc_lcc": microcalc_lcc,
        "microcalc_rmlo" : microcalc_rmlo,
        "microcalc_lmlo" : microcalc_lmlo,
        "parenchyma_rcc": parenchyma_rcc,
        "pectoralis_rcc": pectoralis_rcc,
        "skin_folds_rcc": skin_folds_rcc,
        "parenchyma_lcc": parenchyma_lcc,
        "pectoralis_lcc": pectoralis_lcc,
        "skin_folds_lcc": skin_folds_lcc,
        "parenchyma_rmlo": parenchyma_rmlo,
        "pectoralis_rmlo": pectoralis_rmlo,
        "skin_folds_rmlo": skin_folds_rmlo,
        "parenchyma_lmlo": parenchyma_lmlo,
        "pectoralis_lmlo": pectoralis_lmlo,
        "skin_folds_lmlo": skin_folds_lmlo,
    }

    return {**translations, **variables}


# Diagnose boxes 
def get_lesion_div(box, color,  birads, score, font_size, border_style, label_mapping):
    """
    Generate a div for a lesion based on its bounding box and properties.
    """
    print(f"GENERATE DIVS {color},  {birads}, {border_style}")
    div = f'''
    <div style="
        position: absolute;
        left: {100 * box[0]}%;
        top: {100 * box[1]}%;
        width: {100 * box[2]}%;
        height: {100 * box[3]}%;
        border: 4px {border_style} {color};
        font-size: {font_size};
        color: {color};
        z-index:{200}
    ">
         <p style="left: 0;
                    top: 0;
                    position: absolute;
                    color: black;
                    text-shadow: 2px 0px 3px rgb(215 215 215);
                    margin: 0;
                    padding: 0 2px;
                    background: {color};
            ">
            {birads}
        </p>
    </div>
    '''
    return div


def get_lesion_shapes(proj_findings, birads_list, microcalc=False):
    """
    Extracts the lesion shapes for the given proj_findings (lesion classes) and BI-RADS categories.
    Returns a single string with all the divs.
    """
    lesion_shapes = []

    if not isinstance(proj_findings, dict):
        print("Unexpected structure.")
        return ''

    # Iterate through each lesion class
    for birads_type in birads_list:
        lesion_list = proj_findings.get(birads_type)
        if isinstance(lesion_list, list) and lesion_list:
            lesion_shapes.append(_get_lesion_shapes(lesion_list, birads_type, microcalc))
        else:
            print(f"No lesions found for {birads_type}.")

    # Join all the divs into a single string
    return ''.join(lesion_shapes)


def _get_lesion_shapes(lesion_list, birads_type, microcalc):
    """
    Generates divs for each lesion in the lesion list based on BI-RADS type 
    """
    if not lesion_list:
        return ''    
    # Define colors and styles based on BI-RADS and lesion types
    colors = {
        'vessels': 'gray',
        'birads2': 'green',
        'birads3': 'orange',
        'birads4': '#f14b16',
        'birads5': 'red',
        'lesionKnown': 'cyan'
    }
    border_style = 'dashed' if microcalc else 'solid'
    font_size = '10px' if microcalc and "2" in birads_type else '14px'

    # Label mapping for display
    label_mapping = {
        'vessels': 'gray',
        'birads2': 'BI-RADS_2',
        'birads3': 'BI-RADS_3',
        'birads4': 'BI-RADS_4',
        'birads5': 'BI-RADS_5',
        'lesionKnown': 'Known'
    }

    shapes = ''  

    for lesion in lesion_list:
        box = lesion.get('box')
        if not box:
            continue

        # Generate the div for this lesion
        shapes += get_lesion_div(
            box, 
            colors.get(birads_type, 'cyan'), 
            label_mapping.get(birads_type, 'Unknown'),  
            lesion.get('score'), 
            font_size, 
            border_style, 
            label_mapping
        )

    return shapes


# Quality contours 
def get_quality_shapes(shapes_list, shape_type, img_width, img_height):
    """
    Generate divs for quality indicators such as parenchyma, pectoralis, and skin folds.
    Handles both bounding boxes and contours.
    """

    quality_shapes = []
    
    colors = {
        'parenchyma': 'blue',
        'pectoralis': 'purple',
        'skinFolds': 'yellow',
    }

    for shape in shapes_list:
        box = shape.get('box', [])
        contours = shape.get('contours', [])


        # If there is a bounding box, draw it
        if box:
            div = f'''
            <div style="
                position: absolute;
                top: {box[1] * 100}%;
                left: {box[0] * 100}%;
                width: {box[2] * 100}%;
                height: {box[3] * 100}%;
                border: 2px solid {colors.get(shape_type, 'black')};
                border-radius: inherit;
                font-size: 10px;
                z-index: 200;
                color: {colors.get(shape_type, 'black')};
            ">
                {shape_type.capitalize()}
            </div>
            '''
            quality_shapes.append(div)

        # when contours, generate an SVG path to draw the shape
        if contours:
            # Iterate over the contour points 
            for contour in contours:
                points = " ".join([f"{x * img_width},{y * img_height}" for x, y in contour])
                svg = f'''
               <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 10;">
                    <polygon points="{points}" style="fill: none; stroke: {colors.get(shape_type, 'black')}; stroke-width: 2;"/>
                </svg>
                '''

                # <svg style="position: absolute;  top: {box[1] * 100}%; left: {box[0] * 100}%; width: {box[2] * 100}%; height: {box[3] * 100}%; z-index: 220; border: 1px solid white;">
                quality_shapes.append(svg)

    return ''.join(quality_shapes)

@app.route('/generate-image')
def generate_image():
    with open('results.json') as f:
        results = json.load(f)
    
    # Pass lesion shapes to the template as needed
    variables = get_report_variables()

    return render_template('report_quality.html', **variables)


def generate_image_html2image(template_name, output_file_name, variables):
    """Generate an image using HTML2Image."""
    # Load the CSS content
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    # Render the template with given variables
    html_string = render_template(template_name, style_sheet_content=style_sheet_content, **variables)

    # Create an Html2Image instance
    hti = Html2Image()
    hti.output_path = os.getcwd()

    # Generate the image
    hti.screenshot(html_str=html_string, save_as=output_file_name, size=(1280, 2000))

    return send_file(output_file_name, as_attachment=True)


# Quality HTML2Image Route
@app.route('/html-2-img-html-to-image')
def generate_image_html2image_quality():
    variables = get_report_variables()
    return generate_image_html2image('report_quality.html', 'quality_report_image_html2image.png', variables)


# Diagnostics HTML2Image Route
@app.route('/html-2-img-diagnostics')
def generate_image_html2image_diagnostics():
    variables = get_report_variables()
    return generate_image_html2image('report_diagnostics.html', 'diagnostics_report_image_html2image.png', variables)


# Pyppeteer 
# Helper function to generate image using Pyppeteer
def generate_image_with_pyppeteer(template_name, output_file_name, variables):
    """Generate an image from HTML using Pyppeteer with the specified template and variables."""
    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    # Render the HTML string with variables
    html_string = render_template(template_name, style_sheet_content=style_sheet_content, **variables)

    # Write the rendered HTML to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_html_file:
        temp_html_file.write(html_string.encode('utf-8'))
        temp_html_path = os.path.abspath(temp_html_file.name)


    # Run the Pyppeteer script as a subprocess to generate the image
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

# Pyppeteer Route for Quality and Diagnostics
@app.route('/pyppeteer-html-to-image')
def generate_image_pyppeteer():
    """Generate an image from rendered HTML for either Quality or Diagnostics report using Pyppeteer."""
    report_type = request.args.get('report_type', 'quality')
    
    # Set template and output file name based on report type
    if report_type == 'diagnostics':
        template_name = 'report_diagnostics.html'
        output_file_name = 'diagnostics_report_image_pyppeteer.png'
    else:
        template_name = 'report_quality.html'
        output_file_name = 'quality_report_image_pyppeteer.png'

    variables = get_report_variables()

    return generate_image_with_pyppeteer(template_name, output_file_name, variables)



# Quality report HTML
@app.route('/report')
def report():
    """Render the report_quality.html with necessary variables."""

    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    variables = get_report_variables()


    return render_template('report_quality.html', style_sheet_content=style_sheet_content, **variables)

# Diagnostics report HTML
@app.route('/diagnostics-report')
def diagnostics():
    """Render the report_diagnostics.html with necessary variables."""

    with open(os.path.join('static', 'style.css')) as f:
        style_sheet_content = f.read()

    variables = get_report_variables()

    return render_template('report_diagnostics.html', style_sheet_content=style_sheet_content, **variables)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
