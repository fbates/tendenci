from django.conf.urls.defaults import patterns, url
from events.feeds import LatestEntriesFeed
from events.forms import EventForm, PlaceForm, Reg8nForm, EventWizard

urlpatterns = patterns('events',                  
    url(r'^$', 'views.index', name="events"),
    url(r'^search/$', 'views.search', name="event.search"),
    url(r'^print-view/(?P<id>\d+)/$', 'views.print_view', name="event.print_view"),
    url(r'^add/$', 'views.add', name="event.add"),

    url(r'^edit/(?P<id>\d+)/$', 'views.edit', name="event.edit"),

    (r'^add-wizard/$', EventWizard([EventForm, PlaceForm, Reg8nForm])),

#    url(r'^edit/place/(?P<id>\d+)/$', 'views.edit_place', name="event.edit.place"),
#    url(r'^edit/sponsors/(?P<id>\d+)/$', 'views.edit_sponsor', name="event.edit.sponsor"),
#    url(r'^edit/speakers/(?P<id>\d+)/$', 'views.edit_speaker', name="event.edit.speaker"),
#    url(r'^edit/organizers/(?P<id>\d+)/$', 'views.edit_organizer', name="event.edit.organizer"),
#    url(r'^edit/registration/(?P<id>\d+)/$', 'views.edit_registration', name="event.edit.registration"),

    url(r'^edit/meta/(?P<id>\d+)/$', 'views.edit_meta', name="event.edit.meta"),

    url(r'^delete/(?P<id>\d+)/$', 'views.delete', name="event.delete"),
    url(r'^feed/$', LatestEntriesFeed(), name='event.feed'),
    url(r'^(?P<id>\d+)/$', 'views.index', name="event"),
)