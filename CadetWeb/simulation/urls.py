from django.conf.urls import patterns, url

from simulation import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^single_start/$', views.single_start, name='single_start'),
    url(r'^component_and_step_setup/$', views.component_and_step_setup, name='component_and_step_setup'),
    url(r'^column_setup/$', views.column_setup, name='column_setup'),
    url(r'^confirm_job/$', views.confirm_job, name='confirm_job'),
    url(r'^graph_setup/$', views.graph_setup, name='graph_setup'),
    url(r'^generate_other_graphs/$', views.generate_other_graphs, name='generate_other_graphs'),
    url(r'^isotherm_setup/$', views.isotherm_setup, name='isotherm_setup'),
    url(r'^job_setup/$', views.job_setup, name='job_setup'),
    url(r'^loading_setup/$', views.loading_setup, name='loading_setup'),
    url(r'^performance_parameters/$', views.performance_parameters, name='performance_parameters'),
    url(r'^run_job/$', views.run_job, name='run_job'),
    url(r'^run_job_get/$', views.run_job_get, name='run_job_get'),
    url(r'^sensitivity_setup/$', views.sensitivity_setup, name='sensitivity_setup'),
    url(r'^simulation_setup/$', views.simulation_setup, name='simulation_setup'),
    url(r'^choose_attributes_to_modify/$', views.choose_attributes_to_modify, name='choose_attributes_to_modify'),
    url(r'^choose_search_query/$', views.choose_search_query, name='choose_search_query'),
    url(r'^create_batch_simulation/$', views.create_batch_simulation, name='create_batch_simulation'),
    url(r'^modify_attributes/$', views.modify_attributes, name='modify_attributes'),
    url(r'^inlet_graph/$', views.inlet_graph, name='inlet_graph'),
    url(r'^query_options/$', views.query_options, name='query_options'),
    url(r'^query_results/$', views.query_results, name='query_results'),
    url(r'^get_data/$', views.get_data, name='get_data'),
)