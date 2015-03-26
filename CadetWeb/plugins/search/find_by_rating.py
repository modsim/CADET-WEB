__author__ = 'kosh_000'
name = "Find by Rating"

def run():
    html_string = '''
    <div class="row">
        <div class="col-md-12">
            <div class="form-group">
              <div class="col-sm-2">
                <label for="lb" class="control-label">Lower Bound</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" placeholder="4" name="lb" id="lb">
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-2">
                <label for="ub" class="control-label">Upper Bound</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" placeholder="5" name="ub" id="ub">
              </div>
            </div>
        </div>
      </div>
      '''
    return html_string

def process_search(search_dict):
    search_results = [('JOBID',)]
    search_results.append( (1,))
    search_results.append( (2,))
    return search_results
