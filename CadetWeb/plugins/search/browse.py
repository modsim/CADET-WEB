__author__ = 'kosh_000'
name = "Browse"
form_id = "Browse"
search_name ='Browse Now'

from simulation import models
import settings

def run(request):
    html_string = ''
    return html_string

def process_search(request, search_dict):
    
    search = {}
    if not request.user.groups.filter(name='full_search').exists():
        search['username__in'] = [request.user.username] + list(settings.users_keep)

    results = models.Job.objects.filter(**search)

    headers = ('JOBID',)
    search_results = []
    for result in results:
        search_results.append( (result.id, ))
    return headers, search_results

def get_form(request):
    return name, form_id, run(request), search_name, __name__