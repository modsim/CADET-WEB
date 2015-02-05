name = "Steric Mass Action"
cadet_name = "STERIC_MASS_ACTION"

def run(list_of_names, data):
    html = ['<div class="row"><div class="col-md-12"><table class="table"><thead><tr><th>#</th>']
    for name in list_of_names:
        html.append('<th>%s</th>' % name)
    
    html.append('</tr></thead><tbody>')
    
    for attribute in ('SMA_KA', 'SMA_KD', 'SMA_NU', 'SMA_SIGMA'):
        html.append('<tr><td>%s</td>' % attribute)
        for name in list_of_names:
            value = data.get('%s:%s' % (name, attribute), '0')
            html.append('<td><input type="text" class="required" value="%s" name="%s:%s"></td>' % (value, name, attribute))
        html.append('</tr>')        
    html.append('</tbody></table></div></div>')
    
    html.append('''<div class="row"><div class="col-md-12">
            <div class="form-group">
              <div class="col-sm-2">
                <label for="LAMBDA" class="control-label">SMA_LAMBDA</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control required" id="SMA_LAMBDA" name="SMA_LAMBDA" aria-required="true" value="%s">
              </div>
            </div>
            </div>
            </div>''' % data.get('SMA_LAMBDA', '0'))

    checked_yes = 'checked' if data.get('IS_KINETIC', '') == '1' else ''
    checked_no = '' if data.get('IS_KINETIC', '') == '1' else 'checked'
    html.append('''<div class="row"><div class="col-md-12">
                <div class="form-group">
              <div class="col-sm-offset-2 col-sm-10">
              <div class="radio">
                <input type="radio" name="IS_KINETIC" id="radio1" value="1" %s><label for="radio1">Use Kinetic Model</label>
                <input type="radio" name="IS_KINETIC" id="radio2" value="0" %s><label for="radio2">Don't Use Kinetic Model</label>
                </div>
              </div>
            </div>
            </div></div>''' % (checked_yes, checked_no))

    html = '\n'.join(html)
    return html

def get_suffix_data(suffix, components, data):
    "return all the data that shares a common suffix with the component name"
    return [data['%s:%s' % (component, suffix)] for component in components]

def process_form(list_of_names, form_dict):
    processed_dict = {}
    processed_dict['ISOTHERM'] = cadet_name
    processed_dict['SMA_KA'] = get_suffix_data('SMA_KA', list_of_names, form_dict)
    processed_dict['SMA_KD'] = get_suffix_data('SMA_KD', list_of_names, form_dict)
    processed_dict['SMA_NU'] = get_suffix_data('SMA_NU', list_of_names, form_dict)
    processed_dict['SMA_SIGMA'] = get_suffix_data('SMA_SIGMA', list_of_names, form_dict)
    processed_dict['SMA_LAMBDA'] = form_dict['SMA_LAMBDA']
    processed_dict['IS_KINETIC'] = form_dict['IS_KINETIC']
    return processed_dict

def sensitivity():
    temp = []
    temp.append(['SMA_KA', '1', '0', 'SMA KA'])
    temp.append(['SMA_KD', '1', '0', 'SMA KD'])
    temp.append(['SMA_NU', '1', '0', 'SMA NU'])
    temp.append(['SMA_SIGMA', '1', '0', 'SMA SIGMA'])
    temp.append(['SMA_LAMBDA', '0', '0', 'SMA LAMBDA'])
    return temp