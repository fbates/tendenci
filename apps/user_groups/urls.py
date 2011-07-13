from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('user_groups.views',
    url(r'^$',                              'group_search',     name='groups'),
    url(r'^add/$',                          'group_add_edit', name='group.add'),
    url(r'^search/$',                       'group_search',   name='group.search'),
    url(r'^edit_perms/(?P<id>\d+)/$',       'group_edit_perms', name="group.edit_perms"),
    url(r'^delete/(?P<id>\d+)/$',       'group_delete', name="group.delete"),
    url(r'^(?P<group_slug>[-.\w]+)/$',      'group_detail',   name='group.detail'),
    url(r'^(?P<group_slug>[-.\w]+)/export/members/$', 'group_member_export', name='group.member_export'),
    url(r'^(?P<group_slug>[-.\w]+)/export/subscribers/$', 'group_subscriber_export', name='group.subscriber_export'),
    url(r'^(?P<group_slug>[-.\w]+)/export/all/$', 'group_all_export', name='group.all_export'),
    url(r'^(?P<group_slug>[-.\w]+)/edit/$', 'group_add_edit', name='group.edit'),
    url(r'^(?P<group_slug>[-.\w]+)/adduser/$', 'groupmembership_bulk_add', name='group.adduser'),
    url(r'^(?P<group_slug>[-.\w]+)/edituser/(?P<user_id>\d+)/$', 'groupmembership_add_edit', name='group.edituser'),
    url(r'^(?P<slug>[-.\w]+)/selfadd/(?P<user_id>\d+)/$', 'group_membership_self_add', name='group.selfadd'),
    url(r'^(?P<slug>[-.\w]+)/selfremove/(?P<user_id>\d+)/$', 'group_membership_self_remove', name='group.selfremove'),
    url(r'^(?P<group_slug>[-.\w]+)/deleteuser/(?P<user_id>\d+)/$', 'groupmembership_delete', name='group.deleteuser'),
)
