from django.shortcuts import render_to_response
from django.http import Http404
from django.template import RequestContext

from base.http import render_to_403
from site_settings.models import Setting
from site_settings.forms import build_settings_form

# temporary
def list(request, scope, scope_category, template_name="site_settings/list.html"):
    if not request.user.has_perm('site_settings.change_setting'):
        return render_to_403()
    
    settings = Setting.objects.filter(scope=scope, scope_category=scope_category)
    if not settings:
        raise Http404
    
    if request.method == 'POST':
        form = build_settings_form(request.user, settings)(request.POST)
        if form.is_valid():
            # this save method is overriden in the forms.py
            form.save() 
    else:
        form = build_settings_form(request.user, settings)()
        
    return render_to_response(template_name, {'form': form }, context_instance=RequestContext(request))

def index(request, template_name="site_settings/settings.html"):
    if not request.user.has_perm('site_settings.change_setting'):
        return render_to_403()
    settings = Setting.objects.all().order_by('scope')
    return render_to_response(template_name, {'settings':settings}, context_instance=RequestContext(request))
    