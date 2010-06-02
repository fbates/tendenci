from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, get_host, HttpResponse, Http404, QueryDict
from django.template import RequestContext
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings

from photologue.models import *
from photos.models import Image, Pool, PhotoSet
from photos.forms import PhotoUploadForm, PhotoEditForm, PhotoSetAddForm, PhotoSetEditForm
from django.core import serializers

def details(request, id, set_id=0, template_name="photos/details.html"):
    """ show the photo details """
    
    photo = get_object_or_404(Image, id=id)
    set_id = int(set_id)

    # if not public
    if not photo.is_public:
        # if no permission; raise 404 exception
        if not photo.check_perm(request.user,'photos.view_image'):
            raise Http404
    
    photo_url = photo.get_large_url()
    
    if photo.member == request.user:
        is_me = True
    else:
        is_me = False
    
    return render_to_response(template_name, {
        "photo": photo,
        "photo_url": photo_url,
        "photo_set_id": set_id,
        "is_me": is_me,
    }, context_instance=RequestContext(request))

def photo(request, id, set_id=0, template_name="photos/details.html"):
    """ photo details """
    photo = get_object_or_404(Image, id=id)
    photo_sets = []
    set_id = int(set_id)

    # if private
    if not photo.is_public:
        # if no permission; raise 404 exception
        if not photo.check_perm(request.user,'photos.view_image'):
            raise Http404

    # default set to blank
    photo_prev_url = photo_next_url = ''

    if set_id:
        photo_set = get_object_or_404(PhotoSet, id=set_id)
        photo_prev = photo.get_prev(set=set_id)
        photo_next = photo.get_next(set=set_id)            

        if photo_prev: photo_prev_url = reverse("photo", args= [photo_prev.id, set_id])
        if photo_next: photo_next_url = reverse("photo", args= [photo_next.id, set_id])

        photo_sets = list(photo.photoset.all())
        if photo_set in photo_sets:
            photo_sets.remove(photo_set)
            photo_sets.insert(0, photo_set)
        else:
            set_id = 0
    else:
        photo_prev = photo.get_prev()
        photo_next = photo.get_next()

        if photo_prev: photo_prev_url = reverse("photo", args= [photo_prev.id])
        if photo_next: photo_next_url = reverse("photo", args= [photo_next.id])  

        photo_sets = photo.photoset.all()

    # "is me" variable
    is_me = photo.member == request.user
    
    return render_to_response(template_name, {
        "photo_prev_url": photo_prev_url,
        "photo_next_url": photo_next_url,
        "photo": photo,
        "photo_sets": photo_sets,
        "photo_set_id": set_id,
        "is_me": is_me,
    }, context_instance=RequestContext(request))


@login_required
def memberphotos(request, username, template_name="photos/memberphotos.html", group_slug=None, bridge=None):
    """ Get the members photos and display them """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    user = get_object_or_404(User, username=username)
    
    photos = Image.objects.filter(
        member__username = username,
        is_public = True,
    )
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photos = photos.order_by("-date_added")
    
    return render_to_response(template_name, {
        "group": group,
        "photos": photos,
    }, context_instance=RequestContext(request))


@login_required
def edit(request, id, set_id=0, form_class=PhotoEditForm, template_name="photos/edit.html"):
    """ edit photo view """

    # get photo
    photo = get_object_or_404(Image, id=id)
    set_id = int(set_id)

    # if no permission; raise 404 exception
    if not photo.check_perm(request.user,'photos.change_image'):
        raise Http404

    # get available photo sets
    photo_sets = PhotoSet.objects.all()

    if request.method == "POST":
        if photo.member != request.user: # no permission
            request.user.message_set.create(message="You can't edit photos that aren't yours")
            return HttpResponseRedirect(reverse('photo', args=(photo.id, set_id)))
        if request.POST["action"] == "update":
            photo_form = form_class(request.user, request.POST, instance=photo)
            if photo_form.is_valid():
                photoobj = photo_form.save()
                request.user.message_set.create(message=_("Successfully updated photo '%s'") % photo.title)
                include_kwargs = {"id": photo.id, "set_id": set_id}
                redirect_to = reverse("photo", kwargs=include_kwargs)
                return HttpResponseRedirect(redirect_to)
        else:
            photo_form = form_class(instance=photo)

    else:
        photo_form = form_class(instance=photo)

    return render_to_response(template_name, {
        "photo_form": photo_form,
        "photo": photo,
        "photo_sets": photo_sets,
    }, context_instance=RequestContext(request))

@login_required
def destroy(request, id):
    """ delete photo """

    photo = get_object_or_404(Image, id=id)
    # if no permission; raise 404 exception
    if not photo.check_perm(request.user,'photos.delete_image'):
        raise Http404

    print "request.method:", request.method

    if request.method == "POST":
        request.user.message_set.create(message=_("Successfully deleted photo '%s'") % photo.title)
        photo.delete()
        return HttpResponseRedirect(reverse("photos"))

    return render_to_response("photos/delete.html", {
        "photo": photo,
    }, context_instance=RequestContext(request))

@login_required
def photoset_add(request, form_class=PhotoSetAddForm, template_name="photos/photo-set/add.html"):
    """ Add a photo set """

    # if no permission; raise 404 exception
    if not request.user.has_perm('photos.add_photoset'):
        raise Http404

    if request.method == "POST":
        if request.POST["action"] == "add":

            photoset_form = form_class(request.user, request.POST)
            if photoset_form.is_valid():
                photo_set = photoset_form.save(commit=False)
                photo_set.author = request.user
                photo_set.save()

                request.user.message_set.create(message=_("Successfully added photo set!") + '')
                return HttpResponseRedirect(reverse('photos_batch_add', kwargs={'photoset_id':photo_set.id}))
    else:
        photoset_form = form_class()

    return render_to_response(template_name, {
        "photoset_form": photoset_form,
    }, context_instance=RequestContext(request))


@login_required
def photoset_edit(request, id, form_class=PhotoSetEditForm, template_name="photos/photo-set/edit.html"):
    photo_set = get_object_or_404(PhotoSet, id=id)

    # if no permission; raise 404 exception
    if not photo_set.check_perm(request.user,'photos.change_photoset'):
        raise Http404
    
    if request.method == "POST":
        if request.POST["action"] == "edit":
            photoset_form = form_class(request.user, request.POST, instance=photo_set)
            if photoset_form.is_valid():
                photo_set = photoset_form.save()
                request.user.message_set.create(message=_("Successfully updated photo set! ") + '')
                
                return HttpResponseRedirect(reverse('photoset_latest',))
    else:
        photoset_form = form_class(instance=photo_set)

    return render_to_response(template_name, {
        "photoset_form": photoset_form,
    }, context_instance=RequestContext(request))

@login_required
def photoset_delete(request, id, template_name="photos/photo_set/delete.html"):
    photo_set = get_object_or_404(PhotoSet, id=id)

    # if no permission; raise 404 exception
    if not photo_set.check_perm(request.user,'photos.delete_photoset'):
        raise Http404

    photo_set.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', None))

def photoset_view_latest(request, template_name="photos/photo-set/latest.html"):
    """ View latest photo set """
    q = request.GET.get('q', '')
#    q = SearchQuerySet().query.clean(q) # clean query
#    photo_sets = SearchQuerySet().models(PhotoSet)

    photo_sets = PhotoSet.objects.all()

#    photo_sets = PhotoSet.objects.all()
#    if q: photo_sets = photo_sets.filter(content=q)
#    else: photo_sets = photo_sets.order_by('-photoset_create_dt')
#
#    # not authenticated; limit view
#    if not request.user.has_perm('photos.view_photoset'):
#        photo_sets = photo_sets.filter(publish_type=1) # public photo sets only
        
    return render_to_response(template_name, {"photo_sets": photo_sets, "q": q }, 
        context_instance=RequestContext(request))

@login_required
def photoset_view_yours(request, template_name="photos/photo-set/yours.html"):
    """ View your photo set """
    photo_sets = PhotoSet.objects.all()
    return render_to_response(template_name, {
        "photo_sets": photo_sets,
    }, context_instance=RequestContext(request))

@login_required
def photos_batch_add(request, photoset_id=0):
    """
    params: request, photoset_id
    returns: HttpResponse

    on flash request:
        photoset_id is passed via request.POST
        and received as type unicode and i convert to type integer
    on http request:
        photoset_id is passed via url
    """

    # if no permission; raise 404 exception
    if not request.user.has_perm('photos.view_image'):
        raise Http404

    if request.method == 'POST':

        for field_name in request.FILES:
            uploaded_file = request.FILES[field_name]

            # use file to create title; remove extension
            clean_filename = uploaded_file.name[::-1].split(".", 1)[1][::-1]
            request.POST.update({'title': clean_filename, })

            # get photo-set-id through post parameters
            # get unicode and convert to type integer
            photoset_id = int(request.POST["photoset_id"])

        photo_form = PhotoUploadForm(request.user, request.POST, request.FILES)

        if photo_form.is_valid():

            # save photo
            photo = photo_form.save(commit=False)
            photo.member = request.user
            photo.safetylevel = 3
            photo.save()

            # add to photo set if photo set is specified
            if photoset_id:
                photo_set = get_object_or_404(PhotoSet, id=photoset_id)
                photo_set.image_set.add(photo)

            data = serializers.serialize("json", Image.objects.filter(id=photo.id))

            # returning a response of "ok" (flash likes this)
            # response is for flash, not humans
            return HttpResponse(data, mimetype="text/plain")
        else:
            return HttpResponse("photo is not valid", mimetype="text/plain")

    else:

        if not photoset_id:
            HttpResponseRedirect(reverse('photoset_latest'))

        photo_set = get_object_or_404(PhotoSet, id=photoset_id)

        # show the upload UI
        return render_to_response('photos/batch-add.html', {
            "photoset_id":photoset_id,
            "photo_set": photo_set,
             },
            context_instance=RequestContext(request))

def photos_batch_edit(request, photoset_id=None, form_class=PhotoEditForm,
    template_name="photos/batch-edit.html"):
    """ batch edit photos """
    from django.forms.models import modelformset_factory

    # photo form set
    PhotoFormSet = modelformset_factory(Image, exclude=('title_slug',), extra=0)

    if request.method == "POST":

        photo_formset = PhotoFormSet(request.POST)

        if photo_formset.is_valid():

            photos = photo_formset.save(commit=False)
            for photo in photos:
                photo.member = request.user
                photo.safetylevel = 1
                photo.save()
                
            photo_formset.save_m2m()

        if photoset_id:
            return HttpResponseRedirect(reverse('photoset_details', args=[photoset_id]))  
        else: return HttpResponseRedirect(reverse('photos'))

    else:

        if photoset_id:

            photo_set = get_object_or_404(PhotoSet, id=photoset_id)

            # if permission; get photos for editing
            photo_set = get_object_or_404(PhotoSet, id=photoset_id)
            if photo_set.check_perm(request.user, 'photos.change_photoset'):
                # my photos in this photo set
                photo_queryset = Image.objects.filter(Q(photoset=photoset_id, safetylevel=3, member=request.user))
                photo_queryset = photo_queryset.order_by("-date_added")

                if photo_queryset.count() <= 0:
                    # my photos in this photo set
                    photo_queryset = Image.objects.filter(Q(photoset=photoset_id, member=request.user))
                    photo_queryset = photo_queryset.order_by("-date_added")                    

            else: raise Http404
        else:
            # if permission; get photos for editing
            if request.user.has_perm('photos.change_photoset'):
                # my latest uploaded photos
                photo_queryset = Image.objects.filter(Q(safetylevel=3, member=request.user))
                photo_queryset = photo_queryset.order_by("-date_added")[:60] # limit when pulling all
            else: raise Http404

        photo_formset = PhotoFormSet(queryset=photo_queryset)

 
    return render_to_response(template_name, {
        "photo_formset": photo_formset,
        "photo_set": photo_set,
    }, context_instance=RequestContext(request))


def photoset_details(request, id, template_name="photos/photo-set/details.html"):
    """ View photos in photo set """

    photo_set = get_object_or_404(PhotoSet, id=id)
    photos = photo_set.image_set.all().order_by('date_added', 'id')

    # if private; set private message
    if photo_set.publish_type == 2:
        # if no permission; raise 404 exception
        if not photo_set.check_perm(request.user,'photos.view_photoset'):
            raise Http404 # raise 404 exception
        request.user.message_set.create(message=unicode(_("This photo set is currently in private mode.")))

    return render_to_response(template_name, {
        "photos": photos,
        "photo_set": photo_set,
    }, context_instance=RequestContext(request))
    
    
    
    