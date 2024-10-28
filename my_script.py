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
        print('Translations not found.')
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
    
    # Fetch opacities for lesions
    opacities_rcc = results.get('opacities', {}).get('bbox', {}).get('rcc', {})
    opacities_lcc = results.get('opacities', {}).get('bbox', {}).get('lcc', {})
    opacities_rmlo = results.get('opacities', {}).get('bbox', {}).get('rmlo', {})
    opacities_lmlo = results.get('opacities', {}).get('bbox', {}).get('lmlo', {})

    # Fetch quality indicators for each projection
    quality_rcc = results.get('quality', {}).get('bbox', {}).get('rcc', {})
    quality_lcc = results.get('quality', {}).get('bbox', {}).get('lcc', {})
    quality_rmlo = results.get('quality', {}).get('bbox', {}).get('rmlo', {})
    quality_lmlo = results.get('quality', {}).get('bbox', {}).get('lmlo', {})

    lesion_types = ['birads2', 'birads3', 'birads4', 'birads5', 'lesionKnown']
    
    # Get lesion shapes for each projection
    rectangles_rcc = get_lesion_shapes(opacities_rcc, lesion_types)
    rectangles_lcc = get_lesion_shapes(opacities_lcc, lesion_types)
    rectangles_rmlo = get_lesion_shapes(opacities_rmlo, lesion_types)
    rectangles_lmlo = get_lesion_shapes(opacities_lmlo, lesion_types)

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
        'rectangles_rcc' : rectangles_rcc,
        "rectangles_lcc": rectangles_lcc,
        "rectangles_rmlo" : rectangles_rmlo,
        "rectangles_lmlo" : rectangles_lmlo,
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

def get_lesion_div(box, color, border_radius, birads, score, font_size, border_style, label_mapping):
    """
    Generate a div for a lesion based on its bounding box and properties.
    """

    div = f'''
    <div style="
        position: absolute;
        left: {100 * box[0]}%;
        top: {100 * box[1]}%;
        width: {100 * box[2]}%;
        height: {100 * box[3]}%;
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

    # Loop through the lesions in the lesion list
    for lesion in lesion_list:
        box = lesion.get('box')
        if not box:
            print(f"No box found for lesion {lesion}")
            continue

        # Generate the div for this lesion
        shapes += get_lesion_div(
            box, 
            colors.get(birads_type, 'red'), 
            border_radius, 
            label_mapping.get(birads_type, 'Unknown'),  
            lesion.get('score'), 
            font_size, 
            border_style, 
            label_mapping
        )

    return shapes

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
    
    # Define the list of BI-RADS categories you're interested in
    birads_list_opac = ['birads2', 'birads3', 'birads4', 'birads5', 'lesionKnown']

    # Extract the lesion shapes for each projection
    opacities_rcc = results.get('opacities', {}).get('bbox', {}).get('rcc', {})
    rectangles_rcc = get_lesion_shapes(opacities_rcc, birads_list_opac)
    # Pass lesion shapes to the template as needed
    variables = get_report_variables()
    variables['rectangles_rcc'] = rectangles_rcc

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


# Quality Pyppeteer Route
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
