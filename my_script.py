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

def get_module_icon(currentStatus):
    status_bool = currentStatus == "True" if isinstance(currentStatus, str) else bool(currentStatus)
    return "&#10004;" if status_bool else "&#10008;"

def get_module_status(currentStatus):
    status_bool = currentStatus == "True" if isinstance(currentStatus, str) else bool(currentStatus)
    return translations["confirmed"] if status_bool else translations["not_confirmed"]

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


# Variables 
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

    with open("results.json", "r") as json_file:
        results = json.load(json_file)
    
    exam_details = results
    opacities_lesions = results.get('opacities', {})

    # Density 
    density_rcc = results.get('density', {}).get('rcc', {})
    density_lcc = results.get('density', {}).get('lcc', {})
    density_rmlo = results.get('density', {}).get('rmlo', {})
    density_lmlo = results.get('density', {}).get('lmlo', {})

    # Quality 
    quality_rcc = results.get('quality', {}).get('rcc', {})
    quality_lcc = results.get('quality', {}).get('lcc', {})
    quality_rmlo = results.get('quality', {}).get('rmlo', {})
    quality_lmlo = results.get('quality', {}).get('lmlo', {})

    # Quality features Contours (parenchyma, pectoralis, skin folds)  
    parenchyma_contours_rcc = get_quality_shapes(quality_rcc.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_contours_rcc = get_quality_shapes(quality_rcc.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_contours_rcc = get_quality_shapes(quality_rcc.get('skin_folds', []) or [], 'skinFolds', img_width, img_height)

    parenchyma_contours_lcc = get_quality_shapes(quality_lcc.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_contours_lcc = get_quality_shapes(quality_lcc.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_contours_lcc = get_quality_shapes(quality_lcc.get('skin_folds', []) or [], 'skinFolds', img_width, img_height)

    parenchyma_contours_rmlo = get_quality_shapes(quality_rmlo.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_contours_rmlo = get_quality_shapes(quality_rmlo.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_contours_rmlo = get_quality_shapes(quality_rmlo.get('skin_folds', []) or [], 'skinFolds', img_width, img_height)

    parenchyma_contours_lmlo = get_quality_shapes(quality_lmlo.get('parenchyma', []) or [], 'parenchyma', img_width, img_height)
    pectoralis_contours_lmlo = get_quality_shapes(quality_lmlo.get('pectoralis', []) or [], 'pectoralis', img_width, img_height)
    skin_folds_contours_lmlo = get_quality_shapes(quality_lmlo.get('skin_folds', []) or [], 'skinFolds', img_width, img_height)

    # TODO: Get Parenchyma cuts , Nipple profile location and PNL
    parenchyma_lateral_cuts_rcc = get_quality_shapes(quality_rcc.get('cuts_lateral_list', []) or [], 'cuts_lateral_list', img_width, img_height)
    parenchyma_medial_cuts_rcc = get_quality_shapes(quality_rcc.get('cuts_medial_list', []) or [], 'cuts_medial_list', img_width, img_height)
    parenchyma_lateral_cuts_lcc = get_quality_shapes(quality_lcc.get('cuts_lateral_list', []) or [], 'cuts_lateral_list', img_width, img_height)
    parenchyma_medial_cuts_lcc = get_quality_shapes(quality_lcc.get('cuts_medial_list', []) or [], 'cuts_medial_list', img_width, img_height)
    parenchyma_cuts_rmlo = get_quality_shapes(quality_rmlo.get('parenchyma_cuts_list', []) or [], 'parenchyma_cuts_list', img_width, img_height)
    parenchyma_cuts_lmlo = get_quality_shapes(quality_lmlo.get('parenchyma_cuts_list', []) or [], 'parenchyma_cuts_list', img_width, img_height)

    # nipple_location_rcc = get_quality_shapes(quality_rcc.get('location_nipple', []) or [], 'location_nipple', img_width, img_height)
    # pnl_lines_rcc = ? 


    # Diagnostics 
    # **TODO: obtain the classes to show on report from env file (so the user set this dynamically)
    opacities_types = ['vessels', 'birads2', 'birads3', 'birads4', 'birads5', ]
    microcalc_types = ['birads2', 'birads3', 'birads4', 'birads5', 'lesionKnown']
    
    # Fetch opacities lesions
    opacities_rcc = results.get('opacities', {}).get('rcc', {})
    opacities_lcc = results.get('opacities', {}).get('lcc', {})
    opacities_rmlo = results.get('opacities', {}).get('rmlo', {})
    opacities_lmlo = results.get('opacities', {}).get('lmlo', {})

    # Fetch microcalc lesions 
    microcalc_rcc = results.get('microcalc', {}).get('rcc', {})
    microcalc_lcc = results.get('microcalc', {}).get('lcc', {})
    microcalc_rmlo = results.get('microcalc', {}).get('rmlo', {})
    microcalc_lmlo = results.get('microcalc', {}).get('lmlo', {})

    # Opacities boxes  
    opacities_rcc = get_lesion_shapes(opacities_rcc, opacities_types)
    opacities_lcc = get_lesion_shapes(opacities_lcc, opacities_types)
    opacities_rmlo = get_lesion_shapes(opacities_rmlo, opacities_types)
    opacities_lmlo = get_lesion_shapes(opacities_lmlo, opacities_types)

    # Microcalc boxes  
    microcalc_rcc = get_lesion_shapes(microcalc_rcc, microcalc_types, microcalc=True)
    microcalc_lcc = get_lesion_shapes(microcalc_lcc, microcalc_types, microcalc=True)
    microcalc_rmlo = get_lesion_shapes(microcalc_rmlo, microcalc_types, microcalc=True)
    microcalc_lmlo = get_lesion_shapes(microcalc_lmlo, microcalc_types, microcalc=True)

    # Group the lesions by projection 
    grouped_boxes, lesion_index_mapping = group_lesions_by_projection(opacities_lesions)

    # Tables for the right and left breasts
    right_breast_table, left_breast_table = create_breast_tables(grouped_boxes, opacities_lesions, lesion_index_mapping)


    variables = {
    'report_title': "Mammography Report",
    'breast_image_alt': "Breast Projection Image",

    # Projections images 
    "rcc_proj_img": rcc_proj_img,
    "lcc_proj_img": lcc_proj_img,
    "rmlo_proj_img": rmlo_proj_img,
    "lmlo_proj_img": lmlo_proj_img,

    # General Examination Information
    "patient_name": exam_details['patient_name'],
    "patient_birth": exam_details['patient_birth'],
    "exam_date": exam_details['exam_date'],
    "exam_type": exam_details["exam_type"],
    "ref_phys": exam_details['ref_phys'],
    "operator_name": exam_details['operator_name'],
    "patient_risk_evaluation": exam_details["patient_risk_evaluation"],
    "udi": exam_details["UDI"],
    "limitations": exam_details["limitations"],
    "risk_description": exam_details["risk_description"],

    # *** DENSITY ***
    "overall_density": exam_details.get("overall_density", '--'),
    "density_confirmed": get_module_status(exam_details.get("density_confirmed", False)),
    "density_confirmed_icon": get_module_icon(exam_details.get("density_confirmed", False)),

    # Density per projection
    "density_rcc": density_rcc,
    "density_lcc": density_lcc,
    "density_rmlo": density_rmlo,
    "density_lmlo": density_lmlo,

    # *** QUALITY *** 
    "quality_system_name": exam_details["quality_system_name"],
    "quality_values": exam_details["quality_values"],
    "overall_quality":  exam_details["overall_quality"],
    "quality_confirmed": get_module_status(exam_details.get("quality_confirmed", False)),
    "quality_confirmed_icon": get_module_icon(exam_details.get("quality_confirmed", False)),

    # b-Quality contours 
    "parenchyma_contours_rcc": parenchyma_contours_rcc,
    "pectoralis_contours_rcc": pectoralis_contours_rcc,
    "skin_folds_contours_rcc": skin_folds_contours_rcc,
    "parenchyma_contours_lcc": parenchyma_contours_lcc,
    "pectoralis_contours_lcc": pectoralis_contours_lcc,
    "skin_folds_contours_lcc": skin_folds_contours_lcc,
    "parenchyma_contours_rmlo": parenchyma_contours_rmlo,
    "pectoralis_contours_rmlo": pectoralis_contours_rmlo,
    "skin_folds_contours_rmlo": skin_folds_contours_rmlo,
    "parenchyma_contours_lmlo": parenchyma_contours_lmlo,
    "pectoralis_contours_lmlo": pectoralis_contours_lmlo,
    "skin_folds_contours_lmlo": skin_folds_contours_lmlo,
    "parenchyma_lateral_cuts_rcc": parenchyma_lateral_cuts_rcc,
    "parenchyma_medial_cuts_rcc": parenchyma_medial_cuts_rcc,
    "parenchyma_lateral_cuts_lcc": parenchyma_lateral_cuts_lcc,
    "parenchyma_medial_cuts_lcc": parenchyma_medial_cuts_lcc,
    "parenchyma_cuts_rmlo": parenchyma_cuts_rmlo,
    "parenchyma_cuts_lmlo": parenchyma_cuts_lmlo,

    # Quality RCC
    "quality_class_rcc": quality_rcc.get('quality', "not available"),
    "quality_explanation_rcc": quality_rcc.get('quality_explanation', "not available"),
    "compression_rcc": quality_rcc.get('compression_class', "not available"),
    "symmetry_rcc": quality_rcc.get('symmetry', "not available"),
    "blur_rcc": quality_rcc.get('blur', "not available"),
    "pnl_rcc": quality_rcc.get('PNL', "not available"),
    "pnl_diff_rcc": quality_rcc.get('pecto_nipple_length', "not available"),
    "nipple_profile_rcc": quality_rcc.get('nipple_profile', "not available"),
    "nipple_deviation_rcc": quality_rcc.get('nipple_deviation', "not available"),
    "nipple_angle_rcc": quality_rcc.get('nipple_angle', "not available"),
    "nipple_rcc": quality_rcc.get('nipple_centered', "not available"),
    "medial_parenchyma_rcc": quality_rcc.get('parenchyma_cuts_medial_list', "not available") ,
    "lateral_parenchyma_rcc": quality_rcc.get('parenchyma_cuts_lateral_list', "not available")  ,
    "pectoralis_rcc": quality_rcc.get('pectoralis_muscle', "not available") ,
    "skin_folds_location_rcc" : (quality_rcc.get('skin_folds', []) or [{}])[0].get('location', "none"),
    "skin_folds_severity_rcc" : (quality_rcc.get('skin_folds', []) or [{}])[0].get('severity', "-"),
    "breast_volume_rcc": quality_rcc.get('volume_diff', "not available"),
    "gross_volume_rcc": quality_rcc.get('breast_volume', "not available"),
    "dose_rcc": quality_rcc.get('dose', "not available"),
    "post_surgery_rcc": ' '.join(quality_rcc.get('post_surgery', "no")),
    "clips_rcc": quality_rcc.get('clips', "none"),

    # Quality LCC
    "quality_class_lcc": quality_lcc.get('quality', "not available"),
    "quality_explanation_lcc": quality_lcc.get('quality_explanation', "not available"),
    "compression_lcc": quality_lcc.get('compression_class', "not available"),
    "symmetry_lcc": quality_lcc.get('symmetry', "not available"),
    "blur_lcc": quality_lcc.get('blur', "not available"),
    "pnl_lcc": quality_lcc.get('PNL', "not available"),
    "pnl_diff_lcc": quality_lcc.get('pecto_nipple_length', "not available"),
    "nipple_profile_lcc": quality_lcc.get('nipple_profile', "not available"),
    "nipple_deviation_lcc": quality_lcc.get('nipple_deviation', "not available"),
    "nipple_angle_lcc": quality_lcc.get('nipple_angle', "not available"),
    "nipple_lcc": quality_lcc.get('nipple_centered', "not available"),
    "medial_parenchyma_lcc": quality_lcc.get('parenchyma_cuts_medial_list', "not available"),
    "lateral_parenchyma_lcc": quality_lcc.get('parenchyma_cuts_lateral_list', "not available"),
    "pectoralis_lcc": quality_lcc.get('pectoralis_muscle', "not available"),
    "skin_folds_location_lcc" : (quality_lcc.get('skin_folds', []) or [{}])[0].get('location', "none"),
    "skin_folds_severity_lcc" : (quality_lcc.get('skin_folds', []) or [{}])[0].get('severity', "-"),
    "breast_volume_lcc": quality_lcc.get('volume_diff', "not available"),
    "gross_volume_lcc": quality_lcc.get('breast_volume', "not available"),
    "dose_lcc": quality_lcc.get('dose', "not available"),
    "post_surgery_lcc": ' '.join(quality_lcc.get('post_surgery', "no")),
    "clips_lcc": quality_lcc.get('clips', "none"),

    # Quality RMLO
    "quality_class_rmlo": quality_rmlo.get('quality', "not available"),
    "quality_explanation_rmlo": quality_rmlo.get('quality_explanation', "not available"),
    "compression_rmlo": quality_rmlo.get('compression_class', "not available"),
    "symmetry_rmlo": quality_rmlo.get('symmetry', "not available"),
    "blur_rmlo": quality_rmlo.get('blur', "not available"),
    "pnl_rmlo": quality_rmlo.get('PNL', "not available"),
    "pnl_diff_rmlo": quality_rmlo.get('pecto_nipple_length', "not available"),
    "nipple_profile_rmlo": quality_rmlo.get('nipple_profile', "not available"),
    "parenchyma_rmlo": quality_rmlo.get('parenchyma_cuts', "not available"),
    "pectoralis_rmlo": quality_rmlo.get('pectoralis_muscle', "not available"),
    "skin_folds_location_rmlo" : (quality_rmlo.get('skin_folds', []) or [{}])[0].get('location', "none"),
    "skin_folds_severity_rmlo" : (quality_rmlo.get('skin_folds', []) or [{}])[0].get('severity', "-"),
    "breast_volume_rmlo": quality_rmlo.get('volume_diff', "not available"),
    "gross_volume_rmlo": quality_rmlo.get('breast_volume', "not available"),
    "dose_rmlo": quality_rmlo.get('dose', "not available"),
    "post_surgery_rmlo": ' '.join(quality_rmlo.get('post_surgery', "no")),
    "clips_rmlo": quality_rmlo.get('clips', "none"),
    "pectoralis_angle_rmlo": quality_rmlo.get('pectoralis_angle', "not available"),
    "pectoralis_shape_rmlo": quality_rmlo.get('pectoralis_shape', "not available"),
    "pectoralis_level_rmlo": quality_rmlo.get('pectoralis_level', "not available"),
    "imf_rmlo": quality_rmlo.get('imf', "not available"),
    "elevation_rmlo": quality_rmlo.get('elevation', "not available"),

    # Quality LMLO
    "quality_class_lmlo": quality_lmlo.get('quality', "not available"),
    "quality_explanation_lmlo": quality_lmlo.get('quality_explanation', "not available"),
    "compression_lmlo": quality_lmlo.get('compression_class', "not available"),
    "symmetry_lmlo": quality_lmlo.get('symmetry', "not available"),
    "blur_lmlo": quality_lmlo.get('blur', "not available"),
    "pnl_lmlo": quality_lmlo.get('PNL', "not available"),
    "pnl_diff_lmlo": quality_lmlo.get('pecto_nipple_length', "not available"),
    "nipple_profile_lmlo": quality_lmlo.get('nipple_profile', "not available"),
    "parenchyma_lmlo": quality_lmlo.get('parenchyma_cuts', "not available"),
    "pectoralis_lmlo": quality_lmlo.get('pectoralis_muscle', "not available"),
    "skin_folds_location_lmlo" : (quality_lmlo.get('skin_folds', []) or [{}])[0].get('location', "none"),
    "skin_folds_severity_lmlo" : (quality_lmlo.get('skin_folds', []) or [{}])[0].get('severity', "-"),
    "breast_volume_lmlo": quality_lmlo.get('volume_diff', "not available"),
    "gross_volume_lmlo": quality_lmlo.get('breast_volume', "not available"),
    "dose_lmlo": quality_lmlo.get('dose', "not available"),
    "post_surgery_lmlo": ' '.join(quality_lmlo.get('post_surgery', "no")),
    "clips_lmlo": quality_lmlo.get('clips', "none"),
    "pectoralis_angle_lmlo": quality_lmlo.get('pectoralis_angle', "not available"),
    "pectoralis_shape_lmlo": quality_lmlo.get('pectoralis_shape', "not available"),
    "pectoralis_level_lmlo": quality_lmlo.get('pectoralis_level', "not available"),
    "imf_lmlo": quality_lmlo.get('imf', "not available"),
    "elevation_lmlo": quality_lmlo.get('elevation', "not available"),

    # *** DIAGNOSTICS ***

    # TODO: Obtain highest Class for microcalc and opacities per BREAST
    "overall_right_opacities": "-",  
    "overall_left_opacities":  "3",
    "overall_right_microcalc":  "4",
    "overall_left_microcalc":  "5",

    "opacities_confirmed": get_module_status(exam_details.get("opacities_confirmed", False)),
    "opacities_confirmed_icon": get_module_icon(exam_details.get("opacities_confirmed", False)),
    "microcalc_confirmed": get_module_status(exam_details.get("microcalc_confirmed", False)),
    "microcalc_confirmed_icon": get_module_icon(exam_details.get("microcalc_confirmed", False)),

    #  TODO: Get highest class per projection 
    "high_rcc_opacities": "-",  
    "high_rcc_microcalc":  "BI-RADS 4",
    "high_lcc_opacities":  "BI-RADS ",
    "high_lcc_microcalc":  "5",
    "high_rmlo_opacities": "-",  
    "high_rmlo_microcalc":  "-",
    "high_lmlo_opacities":  "Nothing found",
    "high_lmlo_microcalc":  "BI-RADS 2",

    # Diagnostics module per proj 
    'opacities_rcc': opacities_rcc,
    "opacities_lcc": opacities_lcc,
    "opacities_rmlo": opacities_rmlo,
    "opacities_lmlo": opacities_lmlo,
    'microcalc_rcc': microcalc_rcc,
    "microcalc_lcc": microcalc_lcc,
    "microcalc_rmlo": microcalc_rmlo,
    "microcalc_lmlo": microcalc_lmlo,
    "right_breast_table": right_breast_table,
    "left_breast_table": left_breast_table
    }


    return {**translations, **variables}

# b-QUALITY contours 
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


# b-DIAGNOSTICS BOUNDING BOXES 
def get_lesion_div(box, color,  birads,  font_size, border_style):
    """
    Generate a div for a lesion based on its bounding box and properties.
    """
    print(f"Generate boxes: {color},  {birads}, {border_style}")
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
                    width: max-content;
                    top: -12px;
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
        'vessels': 'Vessels',
        'birads2': 'BI-RADS 2',
        'birads3': 'BI-RADS 3',
        'birads4': 'BI-RADS 4',
        'birads5': 'BI-RADS 5',
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
            font_size, 
            border_style, 
        )

    return shapes

# b-DIAGNOSTICS LESION TABLE 
def process_cc_projection(breast, grouped_boxes, projection, birads_key, box, box_index, lesion_index_mapping):
    matched_projection = 'rmlo' if projection == 'rcc' else 'lmlo'
    current_index = len(grouped_boxes[breast]) + 1

    matched_lesion = box.get('match')
    lesion_entry = [
        [projection, birads_key, box_index],
        [matched_projection, matched_lesion[0], matched_lesion[1]] if matched_lesion else None
    ]

    grouped_boxes[breast].append(lesion_entry)
    lesion_index_mapping[f"{projection},{birads_key},{box_index}"] = current_index

    if matched_lesion:
        lesion_index_mapping[f"{matched_projection},{matched_lesion[0]},{matched_lesion[1]}"] = current_index

def process_mlo_projection(breast, grouped_boxes, projection, birads_key, box, box_index, lesion_index_mapping):
    matched_lesion = box.get('match')

    if not matched_lesion:
        current_index = len(grouped_boxes[breast]) + 1
        lesion_entry = [[projection, birads_key, box_index], None]
        grouped_boxes[breast].append(lesion_entry)
        lesion_index_mapping[f"{projection},{birads_key},{box_index}"] = current_index

def group_lesions_by_projection(opacities_lesions):
    grouped_boxes = {'RightBreast': [], 'LeftBreast': []}
    lesion_index_mapping = {}

    for projection, birads_data in opacities_lesions.items():
        if isinstance(birads_data, dict):
            for birads_key, boxes in birads_data.items():
                if isinstance(boxes, list):
                    for box_index, box in enumerate(boxes):
                        # Determine right or left breast based on projection name
                        is_right_breast = 'r' in projection.lower()
                        is_left_breast = 'l' in projection.lower()

                        if is_right_breast or is_left_breast:
                            breast = 'RightBreast' if is_right_breast else 'LeftBreast'
                            process_projection = process_cc_projection if 'cc' in projection else process_mlo_projection
                            process_projection(
                                breast, grouped_boxes, projection, birads_key, box, box_index, lesion_index_mapping
                            )
    return grouped_boxes, lesion_index_mapping

def process_projection(breast, grouped_boxes, projection, birads_key, box, index, lesion_mapping):
    """
    Processes projections and updates `grouped_boxes` with matched or unmatched lesions.
    """
    # Opposite proj for match
    opposite_projection = {
        'rcc': 'rmlo',
        'rmlo': 'rcc',
        'lcc': 'lmlo',
        'lmlo': 'lcc'
    }.get(projection)

    # Check if there is a matching lesion in the opposite projection
    match_found = False
    if box.get('match') and opposite_projection:
        opposite_key = (breast, birads_key, opposite_projection)
        if opposite_key in lesion_mapping:
            # If a match exists in lesion_mapping, use it and remove to avoid duplication
            matched_index = lesion_mapping.pop(opposite_key)["index"]
            grouped_boxes[breast].append([
                [projection, birads_key, index],
                [opposite_projection, birads_key, matched_index]
            ])
            match_found = True

    if not match_found:
        # If no match found, add as unmatched and store in lesion_mapping
        grouped_boxes[breast].append([
            [projection, birads_key, index],
            None
        ])
        lesion_mapping[(breast, birads_key, projection)] = {
            "projection": projection,
            "type": birads_key,
            "index": index
        }

def get_size_and_extra(opacities_lesions, projection, birads_key, index):
    """Fetches the size and extra information from opacities_lesions for a lesion."""
    lesion_info = opacities_lesions.get(projection, {}).get(birads_key, [])[index]
    if lesion_info:
        size = lesion_info.get('size', [None, None])
        
        # Determine extra_info based on the presence of specific keys
        if 'reassigned' in lesion_info:
            prev_class = lesion_info['reassigned'].get('prevClass', 'unknown')
            extra_info = f"{projection} reassigned from {prev_class}"
        elif 'predicted_class' in lesion_info:
            predicted_class = lesion_info.get('predicted_class', 'unknown')
            extra_info = f"Prev class {predicted_class}"
        elif 'assigned' in lesion_info:
            extra_info = "Revised"
        else:
            extra_info = ""
        
        print(f"lesion_info: {lesion_info}, size: {size}, extra_info: {extra_info}")
        return size, extra_info
    return [None, None], ''

def generate_rows(breast_side, grouped_boxes, opacities_lesions, lesion_index_mapping):
    """Creates HTML rows for each lesion based on projection, class, and size."""
    rows = ""
    for lesion in grouped_boxes[breast_side]:
        # Extract first projection details
        proj1, birads_key1, index1 = lesion[0]
        size1, extra1 = get_size_and_extra(opacities_lesions, proj1, birads_key1, index1)
        
        # Format cc and mlo sizes conditionally
        if proj1 in ['rcc', 'lcc']:
            cc_size = f"{size1[0]:.1f} x {size1[1]:.1f}" if size1[0] is not None and size1[1] is not None else f"{size1[0]:.1f}" if size1[0] is not None else f"{size1[1]:.1f}" if size1[1] is not None else '-'
            mlo_size = '-'
        else:  # Assume proj1 is MLO (e.g., rmlo or lmlo)
            mlo_size = f"{size1[0]:.1f} x {size1[1]:.1f}" if size1[0] is not None and size1[1] is not None else f"{size1[0]:.1f}" if size1[0] is not None else f"{size1[1]:.1f}" if size1[1] is not None else '-'
            cc_size = '-'

        # Fetch the table index for the first lesion
        table_index = lesion_index_mapping.get(f"{proj1},{birads_key1},{index1}", index1 + 1)

        # Check if there's a second matched lesion
        if lesion[1]:
            proj2, birads_key2, index2 = lesion[1]
            size2, extra2 = get_size_and_extra(opacities_lesions, proj2, birads_key2, index2)
            
            # Update sizes based on the second projection if applicable
            if proj2 in ['rcc', 'lcc']:
                cc_size = f"{size2[0]:.1f} x {size2[1]:.1f}" if size2[0] is not None and size2[1] is not None else f"{size2[0]:.1f}" if size2[0] is not None else f"{size2[1]:.1f}" if size2[1] is not None else cc_size
            else:  # proj2 is MLO
                mlo_size = f"{size2[0]:.1f} x {size2[1]:.1f}" if size2[0] is not None and size2[1] is not None else f"{size2[0]:.1f}" if size2[0] is not None else f"{size2[1]:.1f}" if size2[1] is not None else mlo_size
                
            extra_info = extra1 or extra2  # Combine extra info if available

            # Matched lesions in one row
            rows += f"""
            <tr>
                <td>{table_index}</td>
                <td>{birads_key1}</td>
                <td class="size-row">{cc_size}</td>
                <td class="size-row">{mlo_size}</td>
                <td>{extra_info or '-'}</td>
            </tr>
            """
        else:
            # Single entry, no matched lesion
            extra_info = extra1
            rows += f"""
            <tr>
                <td>{table_index}</td>
                <td>{birads_key1}</td>
                <td class="size-row">{cc_size}</td>
                <td class="size-row">{mlo_size}</td>
                <td>{extra_info or '-'}</td>
            </tr>
            """
    return rows

def create_breast_tables(new_grouped_boxes, opacities_lesions, lesion_index_mapping):
    """Generates HTML tables for Right Breast and Left Breast based on projection data."""
    table_template = """
    <table border="0">
        <thead>
            <tr>
                <th>Index</th>
                <th>Class</th>
                <th>CC Size [mm]</th>
                <th>MLO Size [mm]</th>
                <th>Extra Info</th>
            </tr>
        </thead>
        {rows}
    </table>
    """
    
    # Generate rows for each breast side
    right_breast_rows = generate_rows('RightBreast', new_grouped_boxes, opacities_lesions, lesion_index_mapping)
    left_breast_rows = generate_rows('LeftBreast', new_grouped_boxes, opacities_lesions, lesion_index_mapping)

    # Generate complete tables
    right_breast_table = table_template.format(rows=right_breast_rows)
    left_breast_table = table_template.format(rows=left_breast_rows)

    return right_breast_table, left_breast_table

# GENERATE/EXTRACT REPORT FROM HTML FUNCTIONS 
@app.route('/generate-image')
def generate_image():
    with open('results.json') as f:
        results = json.load(f)

        # TODO (TANIU) def get_report(data: dict, width: int, height: int, opac_show: list, microcalc_show: list) -> string: '''function which takes ALL necessary data and returns the report in HTML"
    
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
    hti.screenshot(html_str=html_string, save_as=output_file_name, size=(1280, 2300))  
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



