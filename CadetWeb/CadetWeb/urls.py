from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'CadetWeb.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    
    url(r'^admin/', include(admin.site.urls)),
    url(r'^simulation/', include('simulation.urls', namespace='simulation') ),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^$', include('simulation.urls')),
)
