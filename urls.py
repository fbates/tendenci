from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

# Django admin
from django.contrib import admin
admin.autodiscover()

# authority permissions
import authority
authority.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {"template": "homepage.html",}, name="home"),
    (r'^admin/', include(admin.site.urls)),
    (r'^avatar/', include('avatar.urls')),
    (r'^articles/', include('articles.urls')),
    (r'^entities/', include('entities.urls')),
    (r'^pages/', include('pages.urls')),
    (r'^users/', include('profiles.urls')),
    (r'^photos/', include('photos.urls')),
    (r'^profiles/', include('profiles.urls')),
    (r'^groups/', include('user_groups.urls')),
    (r'^stories/', include('stories.urls')),
    (r'^news/', include('news.urls')),
    (r'^settings/', include('site_settings.urls')),
    (r'^accounts/', include('accounts.urls')),
)

# Local url patterns for development
try:
    from local_urls import MEDIA_PATTERNS
    urlpatterns += MEDIA_PATTERNS
except ImportError:
    pass