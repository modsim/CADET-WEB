__author__ = 'kosh_000'
name = "Search"
form_id = "Search"
search_name = "Search Now"

from simulation import models

def run(request):
    html_string = '''
    <div class="row">
        <div class="col-md-12">
           <p>Browse all simulations.</p>
        </div>
      </div>
      '''
    return html_string

def process_search(request, search_dict):
    results = models.Job.objects.all()

    headers = ('JOBID',)
    search_results = []
    for result in results:
        search_results.append( (result.id, ))
    return headers, search_results

def get_form(request):
    return name, form_id, run(request), search_name