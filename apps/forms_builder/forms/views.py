from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.template import RequestContext
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.forms.models import inlineformset_factory
from django.contrib import messages

from base.http import Http403
from forms_builder.forms.forms import FormForForm, FormForm
from forms_builder.forms.models import Form, Field, FormEntry
from forms_builder.forms.utils import generate_email_body
from perms.models import ObjectPermission
from event_logs.models import EventLog

@login_required
def add(request, form_class=FormForm, template_name="forms/add.html"):
    if not request.user.has_perm('forms.add_form'):
        raise Http403
    
    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():           
            form_instance = form.save(commit=False)
            # set up the user information
            form_instance.creator = request.user
            form_instance.creator_username = request.user.username
            form_instance.owner = request.user
            form_instance.owner_username = request.user.username
            form_instance.save()

            # assign permissions for selected users
            user_perms = form.cleaned_data['user_perms']
            if user_perms: ObjectPermission.objects.assign(user_perms, form_instance)
            # assign creator permissions
            ObjectPermission.objects.assign(form_instance.creator, form_instance)

            log_defaults = {
                'event_id' : 587100,
                'event_data': '%s (%d) added by %s' % (form_instance._meta.object_name, form_instance.pk, request.user),
                'description': '%s added' % form_instance._meta.object_name,
                'user': request.user,
                'request': request,
                'instance': form_instance,
            }
            EventLog.objects.log(**log_defaults)
                                    
            messages.add_message(request, messages.INFO, 'Successfully added %s' % form_instance)
            return HttpResponseRedirect(reverse('form_field_update', args=[form_instance.pk]))
    else:
        form = form_class(request.user)
       
    return render_to_response(template_name, {'form':form}, 
        context_instance=RequestContext(request))

def edit(request, id, form_class=FormForm, template_name="forms/edit.html"):
    form_instance = get_object_or_404(Form, pk=id)
    
    if not request.user.has_perm('forms.change_form', form_instance):
        raise Http403
        form = form_class(request.user, request.POST, instance=form_instance)
        if form.is_valid():           
            form_instance = form.save(commit=False)
            
            # remove all permissions on the object
            ObjectPermission.objects.remove_all(form_instance)
            # assign new permissions
            user_perms = form.cleaned_data['user_perms']
            if user_perms:
                ObjectPermission.objects.assign(user_perms, form_instance)  
            # assign creator permissions
            ObjectPermission.objects.assign(form_instance.creator, form_instance)
                
            form_instance.save()

            log_defaults = {
                'event_id' : 587200,
                'event_data': '%s (%d) edited by %s' % (form_instance._meta.object_name, form_instance.pk, request.user),
                'description': '%s edited' % form_instance._meta.object_name,
                'user': request.user,
                'request': request,
                'instance': form_instance,
            }
            EventLog.objects.log(**log_defaults)
                        
            messages.add_message(request, messages.INFO, 'Successfully edited %s' % form_instance)
            return HttpResponseRedirect(reverse('form_field_update', args=[form_instance.pk]))
    else:
        form = form_class(request.user, instance=form_instance)
       
    return render_to_response(template_name, {'form':form, 'form_instance':form_instance}, 
        context_instance=RequestContext(request))

@login_required
def update_fields(request, id, template_name="forms/update_fields.html"):
    form_instance = get_object_or_404(Form, id=id)
    
    if not request.user.has_perm('forms.add_form', form_instance):
        raise Http403
    form_class=inlineformset_factory(Form, Field, extra=3)
    
    if request.method == "POST":
        form = form_class(request.POST, instance=form_instance)
        if form.is_valid():           
            form.save()
        
            messages.add_message(request, messages.INFO, 'Successfully updated %s' % form_instance)
            return HttpResponseRedirect(reverse('forms'))
    else:
        form = form_class(instance=form_instance)
       
    return render_to_response(template_name, {'form':form, 'form_instance':form_instance}, 
        context_instance=RequestContext(request))
                
@login_required
def delete(request, id, template_name="forms/delete.html"):
    form_instance = get_object_or_404(Form, pk=id)

    # check permission
    if not request.user.has_perm('forms.delete_form', form_instance):
        raise Http403

    if request.method == "POST":
        messages.add_message(request, messages.INFO, 'Successfully deleted %s' % form_instance)

        log_defaults = {
            'event_id' : 587300,
            'event_data': '%s (%d) deleted by %s' % (form_instance._meta.object_name, form_instance.pk, request.user),
            'description': '%s deleted' % form_instance._meta.object_name,
            'user': request.user,
            'request': request,
            'instance': form_instance,
        }
        EventLog.objects.log(**log_defaults)
            
        form_instance.delete()
        return HttpResponseRedirect(reverse('forms'))

    return render_to_response(template_name, {'form': form_instance},
        context_instance=RequestContext(request))
    
@login_required
def entries(request, id, template_name="forms/entries.html"):
    form = get_object_or_404(Form, pk=id)
    if not request.user.has_perm('forms.change_form', form):
        raise Http403

    entries = form.entries.all()
    
    return render_to_response(template_name, {'form':form,'entries': entries},
        context_instance=RequestContext(request))
    
@login_required
def entry_delete(request, id, template_name="forms/entry_delete.html"):
    entry = get_object_or_404(FormEntry, pk=id)
    
    # check permission
    if not request.user.has_perm('forms.delete_form', entry.form):
        raise Http403

    if request.method == "POST":
        messages.add_message(request, messages.INFO, 'Successfully deleted entry %s' % entry)
        entry.delete()
        return HttpResponseRedirect(reverse('forms'))

    return render_to_response(template_name, {'entry': entry},
        context_instance=RequestContext(request))
    
def entry_detail(request, id, template_name="forms/entry_detail.html"):
    entry = get_object_or_404(FormEntry, pk=id)
    
    # check permission
    if not request.user.has_perm('forms.view_form', entry.form):
        raise Http403
    return render_to_response(template_name, {'entry':entry}, 
        context_instance=RequestContext(request))

def entries_export(request, id):
    form_instance = get_object_or_404(Form, pk=id)
    
    # check permission
    if not request.user.has_perm('forms.change_form', form_instance):
        raise Http403

    log_defaults = {
        'event_id' : 587600,
        'event_data': '%s (%d) exported by %s' % (form_instance._meta.object_name, form_instance.pk, request.user),
        'description': '%s exported' % form_instance._meta.object_name,
        'user': request.user,
        'request': request,
        'instance': form_instance,
    }
    EventLog.objects.log(**log_defaults)
            
    entries = form_instance.entries.all()

    if entries:      
        import csv
        import zipfile
        from os.path import join
        from os import unlink
        from time import time
        from tempfile import NamedTemporaryFile
    
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=export_entries_%d.csv' % time()  
        headers = []
        has_files = False
            
        # check for a field field
        for entry in entries:
            for field in entry.fields.all():
                if field.field.field_type == 'FileField':
                    has_files = True
            
        # if the object hase file store the csv elsewhere
        # so that we can zip the files
        if has_files:
            temp_csv = NamedTemporaryFile(mode='w', delete=False)
            temp_zip = NamedTemporaryFile(mode='wb', delete=False)
            writer = csv.writer(temp_csv, delimiter=',')
            zip = zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED)
        else:
            writer = csv.writer(response, delimiter=',')
                    
        # get the header for headers for the csv
        headers.append('submitted on')
        for field in entries[0].fields.all():
            headers.append(field.field.label)
        writer.writerow(headers)
        
        # write out the values
        for entry in entries:
            values = []
            values.append(entry.entry_time)
            for field in entry.fields.all():
                if has_files and field.field.field_type == 'FileField':
                    file_path = join(settings.MEDIA_ROOT,field.value)
                    archive_name = join('files',field.value)
                    zip.write(file_path, archive_name, zipfile.ZIP_DEFLATED)
                    
                values.append(field.value)
        
            writer.writerow(values)        
        
        # add the csv file to the zip, close it, and set the response
        if has_files:
            # add the csv file and close it all out
            temp_csv.close()
            zip.write(temp_csv.name, 'entries.csv', zipfile.ZIP_DEFLATED)
            zip.close()  
            temp_zip.close()
            
            # set the response for the zip files
            response = HttpResponse(open(temp_zip.name,'rb'), mimetype='application/zip')
            response['Content-Disposition'] = 'attachment; filename=export_entries_%d.zip' % time()  
            
            # remove the temporary files
            unlink(temp_zip.name)
            unlink(temp_csv.name)
    else:
        # blank csv document
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=export_entries_%d.csv' % time()  
        writer = csv.writer(response, delimiter=',')
    
    return response

def search(request, template_name="forms/search.html"):
    query = request.GET.get('q', None)
    forms = Form.objects.search(query, user=request.user)
    
    return render_to_response(template_name, {'forms':forms}, 
        context_instance=RequestContext(request))


def form_detail(request, slug, template="forms/form_detail.html"):
    """
    Display a built form and handle submission.
    """    
    published = Form.objects.published(for_user=request.user)
    form = get_object_or_404(published, slug=slug)

    if not request.user.has_perm('forms.view_form', form):
        raise Http403
    
    form_for_form = FormForForm(form, request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form_for_form.is_valid():
            entry = form_for_form.save()
            email_headers = {'Content-Type': 'text/html'}
#            fields = ["%s: %s" % (v.label, form_for_form.cleaned_data[k]) 
#                for (k, v) in form_for_form.fields.items()]
            subject = "%s - %s" % (form.title, entry.entry_time.strftime('%m-%d-%Y %H:%M'))
            # body = "\n".join(fields)
            body = generate_email_body(entry)
            email_from = form.email_from or settings.DEFAULT_FROM_EMAIL
            email_to = form_for_form.email_to()
            if email_to and form.send_email:
                msg = EmailMessage(subject, body, email_from, [email_to], headers=email_headers)
                msg.content_subtype = 'html'
                msg.send()
            email_from = email_to or email_from # Send from the email entered.
            email_copies = [e.strip() for e in form.email_copies.split(",") 
                if e.strip()]
            if email_copies:
                msg = EmailMessage(subject, body, email_from, email_copies, headers=email_headers)
                msg.content_subtype = 'html'
                for f in form_for_form.files.values():
                    f.seek(0)
                    msg.attach(f.name, f.read())
                msg.send()
            return redirect(reverse("form_sent", kwargs={"slug": form.slug}))
    context = {"form": form, "form_for_form": form_for_form}
    return render_to_response(template, context, RequestContext(request))

def form_sent(request, slug, template="forms/form_sent.html"):
    """
    Show the response message.
    """
    published = Form.objects.published(for_user=request.user)
    form = get_object_or_404(published, slug=slug)
    context = {"form": form}
    return render_to_response(template, context, RequestContext(request))