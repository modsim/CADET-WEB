name = "Thermal Langmuir"
cadet_name = "THERMAL_LANGMUIR"

def run(list_of_names, data):
    html = ['<div class="row"><div class="col-md-12"><table class="table"><thead><tr><th>#</th>']
    for name in list_of_names:
        html.append('<th>%s</th>' % name)
    
    html.append('</tr></thead><tbody>')
    
    for attribute in ('KA', 'KD', 'QMAX'):
        html.append('<tr><td>%s</td>' % attribute)
        for name in list_of_names:
                html.append('<td><input type="text" class="required" value="0" name="%s:%s"></td>' % (name, attribute))
        html.append('</tr>')        
    html.append('</tbody></table></div></div>')

    html = '\n'.join(html)
    return html

def get_suffix_data(suffix, components, data):
    "return all the data that shares a common suffix with the component name"
    return [data['%s_%s' % (component, suffix)] for component in components]

def process_form(list_of_names, form_dict):
    processed_dict = {}
    processed_dict['ISOTHERM'] = cadet_name
    processed_dict['MCL_KA'] = get_suffix_data('KA', list_of_names, form_dict)
    processed_dict['MCL_KD'] = get_suffix_data('KD', list_of_names, form_dict)
    processed_dict['MCL_QMAX'] = get_suffix_data('QMAX', list_of_names, form_dict)
    return processed_dict

def sensitivity():
    temp = []
    temp.append(['MCL_KA', '1', '0', 'MCL KA'])
    temp.append(['MCL_KD', '1', '0', 'MCL KD'])
    temp.append(['MCL_QMAX', '1', '0', 'MCL QMAX'])
    return temp