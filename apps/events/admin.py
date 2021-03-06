from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import iri_to_uri

from events.models import CustomRegForm, CustomRegField
from events.forms import CustomRegFormAdminForm, CustomRegFormForField 
from event_logs.models import EventLog

class EventAdmin(admin.ModelAdmin):
#    form = EventForm
    list_display=(
        'title',
        'description', 
        'start_dt',
        'end_dt',
        'timezone',
        'allow_anonymous_view',
        'allow_user_view',
        'allow_user_edit',
        'status',
        'status_detail',
    )

#admin.site.register(Event, EventAdmin)
#admin.site.register(Type)

class CustomRegFieldAdminForm(CustomRegFormForField):
    class Meta:
        model = CustomRegField

    
class CustomRegFieldAdmin(admin.TabularInline):
    model = CustomRegField    
    form = CustomRegFieldAdminForm
    extra = 0
    ordering = ("position",)

class CustomRegFormAdmin(admin.ModelAdmin):
    inlines = (CustomRegFieldAdmin,)
    list_display = ("name", "preview_link", "for_event", "notes", 'validate_guest', "status",)
    search_fields = ("name", "notes", "status",)
    fieldsets = (
        (None, {"fields": ("name", "notes", 'validate_guest', 'status')}),
    )
    #readonly_fields = ['event']
    
    form = CustomRegFormAdminForm
    
    class Media:
        js = (
            '%sjs/jquery-1.4.2.min.js' % settings.STATIC_URL,
            '%sjs/jquery_ui_all_custom/jquery-ui-1.8.5.custom.min.js' % settings.STATIC_URL,
            #'%sjs/admin/form-fields-inline-ordering.js' % settings.STATIC_URL,
            '%sjs/admin/custom_reg_form_inline_ordering.js' % settings.STATIC_URL,
            '%sjs/global/tinymce.event_handlers.js' % settings.STATIC_URL,
        )
        css = {'all': ['%scss/admin/dynamic-inlines-with-sort.css' % settings.STATIC_URL], }
        
    def preview_link(self, obj):

        return """<a href="%s">preview</a>
            """ % (reverse('event.custom_reg_form_preview', args=[obj.id]))
    preview_link.allow_tags = True
    preview_link.short_description = 'Preview Link'
    
    def for_event(self, obj):
        event = None
        regconf = obj.regconfs.all()[:1]
        if regconf:
            event = regconf[0].event
        regconfpricing = obj.regconfpricings.all()[:1]
        if regconfpricing:
            event = regconfpricing[0].reg_conf.event
        if event:
            return """<a href="%s">%s(ID:%d)</a>
            """ % (reverse('event', args=[event.id]), event.title, event.id)
        return ''
        
    for_event.allow_tags = True
    for_event.short_description = 'For Event'
    
#    def get_fieldsets(self, request, instance=None):
#        """
#        Dynamically generate the fieldset
#        """
#        fields = ['name', 'notes', 'status']
##        if instance and instance.entries.count():
##            
##            # used - indicate the form has been used or is being used
##            fields.append('used')
#
#        field_list = ((None, {'fields': tuple(fields)}),)
#
#        return field_list

    def change_view(self, request, object_id, extra_context=None):
        result = super(CustomRegFormAdmin, self).change_view(request, object_id, extra_context)

        if not request.POST.has_key('_addanother') and not request.POST.has_key('_continue') and request.GET.has_key('next'):
            result['Location'] = iri_to_uri("%s") % request.GET.get('next')
        return result

        
    def save_model(self, request, object, form, change):
        instance = form.save(commit=False)
         
        if not change:
            instance.creator = request.user
            instance.creator_username = request.user.username
            
        instance.owner = request.user
        instance.owner_username = request.user.username

        # save the object
        instance.save()
        
        form.save_m2m()
        
        return instance
    
    def log_deletion(self, request, object, object_repr):
        super(CustomRegFormAdmin, self).log_deletion(request, object, object_repr)
        log_defaults = {
            'event_id' : 176300,
            'event_data': '%s (%d) deleted by %s' % (object._meta.object_name, 
                                                    object.pk, request.user),
            'description': '%s deleted' % object._meta.object_name,
            'user': request.user,
            'request': request,
            'instance': object,
        }
        EventLog.objects.log(**log_defaults)
    
    def log_change(self, request, object, message):
        super(CustomRegFormAdmin, self).log_change(request, object, message)
        log_defaults = {
            'event_id' : 176200,
            'event_data': '%s (%d) edited by %s' % (object._meta.object_name, 
                                                    object.pk, request.user),
            'description': '%s edited' % object._meta.object_name,
            'user': request.user,
            'request': request,
            'instance': object,
        }
        EventLog.objects.log(**log_defaults)
    
    def log_addition(self, request, object):
        super(CustomRegFormAdmin, self).log_addition(request, object)
        log_defaults = {
            'event_id' : 176100,
            'event_data': '%s (%d) added by %s' % (object._meta.object_name, 
                                                   object.pk, request.user),
            'description': '%s added' % object._meta.object_name,
            'user': request.user,
            'request': request,
            'instance': object,
        }
        EventLog.objects.log(**log_defaults)
        
        
admin.site.register(CustomRegForm, CustomRegFormAdmin)
