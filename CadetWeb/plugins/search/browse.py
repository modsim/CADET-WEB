__author__ = 'kosh_000'
name = "Browse"
form_id = "Browse"
search_name ='Browse Now'

from simulation import models

def run(request):
    html_string = ''
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