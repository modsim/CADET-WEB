__author__ = 'kosh_000'
name = "Find by User"
form_id = "FindByUser"

from simulation import models

def run(request):
    if request.user.is_superuser:
        html_string = '''
        <div class="row">
            <div class="col-md-12">
                <div class="form-group">
                  <div class="col-sm-2">
                    <label for="user_name" class="control-label">User Name</label>
                  </div>
                  <div class="col-sm-10">
                    <input type="text" class="form-control required" placeholder="" name="user_name" id="user_name">
                  </div>
            </div>
          </div>
          '''
    else:
        html_string = ''
    return html_string

def process_search(request, search_dict):
    if request.user.is_superuser:
        user_name = search_dict['user_name']
    else:
        user_name = request.user.username

    results = models.Job.objects.filter(username=user_name)

    headers = ('JOBID',)
    search_results = []
    for result in results:
        search_results.append( (result.id, ))
    return headers, search_results

def get_form(request):
    return name, form_id, run(request)
