name = "Find by Yield"

def run():
    html_string = '''
    <div class="row">
        <div class="col-md-12">
            <div class="form-group">
              <div class="col-sm-2">
                <label for="inputEmail3" class="control-label">Minimum Yield</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" id="inputEmail3" placeholder="95%">
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-2">
                <label for="inputPassword3" class="control-label">Maximum Yield</label>
              </div>
              <div class="col-sm-10">
                <input type="text" class="form-control" id="inputPassword3" placeholder="98%">
              </div>
            </div>
        </div>
      </div>
      '''
    return html_string

def process_search(search_dict):
    headers = ('JOBID', 'Yield')
    search_results = []
    search_results.append( (1, '95%'))
    search_results.append( (2, '97%'))
    return headers, search_results