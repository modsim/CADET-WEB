__author__ = 'kosh_000'
name = "Find by Rating"
form_id = "FindByRating"

from simulation import models

def run(request):
    html_string = '''
    <div class="row">
        <div class="col-md-12">
            <div class="form-group">
              <div class="col-sm-2">
                <label for="lb" class="control-label">Lower Bound</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control required" placeholder="4" name="lb" id="lb">
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-2">
                <label for="ub" class="control-label">Upper Bound</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control required" placeholder="5" name="ub" id="ub">
              </div>
            </div>
        </div>
      </div>
      '''
    return html_string

def process_search(request, search_dict):
    lb = float(search_dict['lb'])
    ub = float(search_dict['ub'])

    results = models.Job_Notes.objects.filter(rating__range=(lb, ub))

    headers = ('JOBID',)
    search_results = []
    for result in results:
        search_results.append( (result.Job_ID.id, ))
    return headers, search_results

def get_form(request):
    return name, form_id, run(request)