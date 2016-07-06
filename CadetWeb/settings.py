__author__ = 'kosh_000'

chunk_size = 20

#limits are hard limits, a soft limit will be automatically created
# that is 90% of the given value so the program can shut down

#Limit memory usage in MB
memory = 500

#cpu time in seconds (total time cadet is allowed to run) analysis takes places after this
cpu = 500.0


#limit number of combinations
batch_limit = 45


#days to keep simulations
keep_time = 0

#users to keep records for
users_keep = set(['cadet',])

#time format string according to the python docs. I am defaulting to a time format that should be readable to everyone
#Year Month Day Hour:Minutes:Seconds  with the Month spelled out and without timezone information
time_format = '%Y %B %d  %H:%M:%S'

#how  many examples to show
examples = 10

#allowed isotherms and the order they shoudl be shown in
isotherms = ('MULTI_COMPONENT_LANGMUIR', 'MULTI_COMPONENT_BILANGMUIR', 'EXTERNAL_LANGMUIR', 'STERIC_MASS_ACTION', 'EXTERNAL_STERIC_MASS_ACTION', 'SELF_ASSOCIATION', 'LINEAR', 
             'MOBILE_PHASE_MODULATORS', 'EXTERNAL_MOBILE_PHASE_MODULATORS')

first_component_salt = ( 'STERIC_MASS_ACTION', 'EXTERNAL_STERIC_MASS_ACTION', 'SELF_ASSOCIATION', 'MOBILE_PHASE_MODULATORS', 'EXTERNAL_MOBILE_PHASE_MODULATORS')

#site_url = 'https://ibt761.ibt.kfa-juelich.de'
site_url = 'https://www.cadet-web.de/'
