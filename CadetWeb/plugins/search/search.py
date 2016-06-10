__author__ = 'kosh_000'
name = "Search"
form_id = "Search"
search_name = "Search Now"

from simulation import models
import settings

def run(request):
    html = ['''
    <div class="row">
        <div class="col-md-12">
           <div class="form-group">
              <div class="col-sm-2"><label class="control-label">Search Data Range</label></div>
              <div class="col-sm-1">
                <label for="lb" class="control-label">From</label>
              </div>
              <div class="col-sm-3 date">
                <input type="date" class="form-control" name="lb" id="lb">
              </div>
              <div class="col-sm-1">
                <label for="ub" class="control-label">To</label>
              </div>
              <div class="col-sm-3 date">
                <input type="date" class="form-control" name="ub" id="ub">
              </div>
            </div>''',]

    if request.user.groups.filter(name='full_search').exists():
            html.append('''
            <div class="form-group">
              <div class="col-sm-2">
                <label for="username" class="control-label">Username</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" name="username" id="username">
              </div>
            </div>''',)
    
    html.append('''
            <div class="form-group">
              <div class="col-sm-2">
                <label for="study_name" class="control-label">Study Name</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" name="study_name" id="study_name">
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-2">
                <label for="product_name" class="control-label">Product Name</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" name="product_name" id="product_name">
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-2">
                <label for="model_name" class="control-label">Model Name</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" name="model_name" id="model_name">
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-2">
                <label for="notes" class="control-label">Notes</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" name="notes" id="notes">
              </div>
            </div>
        </div>
      </div>
      ''')
    return ''.join(html)

def process_search(request, search_dict):
    lb = search_dict['lb']
    ub = search_dict['ub']


    if request.user.groups.filter(name='full_search').exists():
        username = search_dict['username']
    study_name = search_dict['study_name']
    product_name = search_dict['product_name']
    model_name = search_dict['model_name']
    notes = search_dict['notes']


    # job_notes__notes__icontains = notes, 
    
    search = {}
    search['study_name__icontains'] = study_name

    if request.user.groups.filter(name='full_search').exists():
        search['username__icontains'] = username
    else:
        search['username__in'] = [request.user.username] + list(settings.users_keep)

    search['Model_ID__model__icontains'] = model_name
    search['Product_ID__product__icontains'] = product_name
    if lb:
        search['created__gt'] = lb
    if ub:
        search['created__lt'] = ub
    if notes:
        search['job_notes__notes__icontains'] = notes
    
    results = models.Job.objects.filter(**search)

    headers = ('JOBID',)
    search_results = []
    for result in results:
        search_results.append( (result.id, ))
    return headers, search_results

def get_form(request):
    return name, form_id, run(request), search_name, __name__