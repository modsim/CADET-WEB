__author__ = 'kosh_000'
name = "Find by Job #"
form_id = "FindByJob"
search_name ="Find Job"

from simulation import models

def run(request):
    html_string = '''
    <div class="row">
        <div class="col-md-12">
            <div class="form-group">
              <div class="col-sm-2">
                <label for="job_id" class="control-label">Job #</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control required" name="job_id" id="job_id">
              </div>
            </div>
           
        </div>
      </div>
      '''
    return html_string

def process_search(request, search_dict):
    headers = ('JOBID',)
    search_results = []

    try:
        job_id = int(search_dict['job_id'])
    except ValueError:
        return headers, search_results

    results = models.Job.objects.filter(id=job_id)


    for result in results:
        search_results.append( (result.id, ))
    return headers, search_results

def get_form(request):
    return name, form_id, run(request), search_name, __name__