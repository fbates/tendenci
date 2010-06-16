from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from base.http import Http403
from locations.models import Location
from locations.forms import LocationForm
from perms.models import ObjectPermission
from event_logs.models import EventLog

def index(request, id=None, template_name="locations/view.html"):
    if not id: return HttpResponseRedirect(reverse('location.search'))
    location = get_object_or_404(Location, pk=id)
    
    if request.user.has_perm('locations.view_location', location):
        log_defaults = {
            'event_id' : 835000,
            'event_data': '%s (%d) viewed by %s' % (location._meta.object_name, location.pk, request.user),
            'description': '%s viewed' % location._meta.object_name,
            'user': request.user,
            'request': request,
            'instance': location,
        }
        EventLog.objects.log(**log_defaults)
        return render_to_response(template_name, {'location': location}, 
            context_instance=RequestContext(request))
    else:
        raise Http403

def search(request, template_name="locations/search.html"):
    query = request.GET.get('q', None)
    locations = Location.objects.search(query)

    log_defaults = {
        'event_id' : 834000,
        'event_data': '%s searched by %s' % ('Location', request.user),
        'description': '%s searched' % 'Location',
        'user': request.user,
        'request': request,
        'source': 'locations'
    }
    EventLog.objects.log(**log_defaults)
    
    return render_to_response(template_name, {'locations':locations}, 
        context_instance=RequestContext(request))

def print_view(request, id, template_name="locations/print-view.html"):
    location = get_object_or_404(Location, pk=id)    

    log_defaults = {
        'event_id' : 835000,
        'event_data': '%s (%d) viewed by %s' % (location._meta.object_name, location.pk, request.user),
        'description': '%s viewed' % location._meta.object_name,
        'user': request.user,
        'request': request,
        'instance': location,
    }
    EventLog.objects.log(**log_defaults)
       
    if request.user.has_perm('locations.view_location', location):
        return render_to_response(template_name, {'location': location}, 
            context_instance=RequestContext(request))
    else:
        raise Http403
    
@login_required
def edit(request, id, form_class=LocationForm, template_name="locations/edit.html"):
    location = get_object_or_404(Location, pk=id)

    if request.user.has_perm('locations.change_location', location):    
        if request.method == "POST":
            form = form_class(request.user, request.POST, instance=location)
            if form.is_valid():
                location = form.save(commit=False)
                location.save()

                log_defaults = {
                    'event_id' : 832000,
                    'event_data': '%s (%d) edited by %s' % (location._meta.object_name, location.pk, request.user),
                    'description': '%s edited' % location._meta.object_name,
                    'user': request.user,
                    'request': request,
                    'instance': location,
                }
                EventLog.objects.log(**log_defaults)
                
                # remove all permissions on the object
                ObjectPermission.objects.remove_all(location)
                
                # assign new permissions
                user_perms = form.cleaned_data['user_perms']
                if user_perms:
                    ObjectPermission.objects.assign(user_perms, location)               
 
                # assign creator permissions
                ObjectPermission.objects.assign(location.creator, location) 
                                                              
                return HttpResponseRedirect(reverse('location', args=[location.pk]))             
        else:
            form = form_class(request.user, instance=location)

        return render_to_response(template_name, {'location': location, 'form':form}, 
            context_instance=RequestContext(request))
    else:
        raise Http403

@login_required
def add(request, form_class=LocationForm, template_name="locations/add.html"):
    if request.user.has_perm('locations.add_location'):
        if request.method == "POST":
            form = form_class(request.user, request.POST)
            if form.is_valid():           
                location = form.save(commit=False)
                # set up the user information
                location.creator = request.user
                location.creator_username = request.user.username
                location.owner = request.user
                location.owner_username = request.user.username
                location.save()
 
                log_defaults = {
                    'event_id' : 831000,
                    'event_data': '%s (%d) added by %s' % (location._meta.object_name, location.pk, request.user),
                    'description': '%s added' % location._meta.object_name,
                    'user': request.user,
                    'request': request,
                    'instance': location,
                }
                EventLog.objects.log(**log_defaults)
                               
                # assign permissions for selected users
                user_perms = form.cleaned_data['user_perms']
                if user_perms:
                    ObjectPermission.objects.assign(user_perms, location)
                
                # assign creator permissions
                ObjectPermission.objects.assign(location.creator, location) 
                
                return HttpResponseRedirect(reverse('location', args=[location.pk]))
        else:
            form = form_class(request.user)
           
        return render_to_response(template_name, {'form':form}, 
            context_instance=RequestContext(request))
    else:
        raise Http403
    
@login_required
def delete(request, id, template_name="locations/delete.html"):
    location = get_object_or_404(Location, pk=id)

    if request.user.has_perm('locations.delete_location'):   
        if request.method == "POST":
            log_defaults = {
                'event_id' : 833000,
                'event_data': '%s (%d) deleted by %s' % (location._meta.object_name, location.pk, request.user),
                'description': '%s deleted' % location._meta.object_name,
                'user': request.user,
                'request': request,
                'instance': location,
            }
            
            EventLog.objects.log(**log_defaults)
            
            location.delete()
                
            return HttpResponseRedirect(reverse('location.search'))
    
        return render_to_response(template_name, {'location': location}, 
            context_instance=RequestContext(request))
    else:
        raise Http403