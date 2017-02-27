import functools
from django.conf.urls import include, url
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

import fedoralink_ui.views
from fedoralink.common_namespaces.dc import DCObject
from fedoralink.models import FedoraObject
from django.conf import settings


# TODO: zbavit sa model = DCObject, pridat template pre detail collection (search)


def repository_patterns(app_name, fedora_prefix='', custom_patterns=None, custom_extended_search_params = None):
    extended_search_params = dict(
        facets=(),
        orderings=(
                 ('title@lang', _('Sort by title (asc)')),
                 ('-title@lang', _('Sort by title (desc)')),
        ),
        title='Documents',
        create_button_title='Create a New Document',
        fedora_prefix=fedora_prefix)

    if custom_extended_search_params:
        for k, v in custom_extended_search_params.items():
            extended_search_params[k] = v

    urlpatterns = [
        url('^$',
            fedoralink_ui.views.GenericDetailView.as_view(
                fedora_prefix=fedora_prefix), name="index"),

        url(r'^((?P<collection_id>.*)/)?extended_search(?P<parameters>.*)$',
             fedoralink_ui.views.GenericSearchView.as_view(**extended_search_params),
             name='extended_search'),

        url('^(?P<id>.*)/addSubcollection$', (fedoralink_ui.views.GenericSubcollectionCreateView.as_view(
            fedora_prefix=fedora_prefix,
            success_url="oarepo:detail",
            parent_collection=lambda x: FedoraObject.objects.get(pk=fedora_prefix),
            success_url_param_names=('id',)
        )), name='addSubcollection'),

        url('^(?P<id>.*)/add$', (fedoralink_ui.views.GenericCreateView.as_view(
            fedora_prefix=fedora_prefix,
            success_url="oarepo:detail",
            parent_collection=lambda x: FedoraObject.objects.get(pk=fedora_prefix),
            success_url_param_names=('id',)
        ))
             , name='add'),

        url('^(?P<id>.*)/edit$',
             (fedoralink_ui.views.GenericEditView.as_view(
                 success_url="oarepo:detail",
                 fedora_prefix=fedora_prefix
             )),
             name="edit"),

        url('^(?P<id>.*)$',
            fedoralink_ui.views.GenericDetailView.as_view(
                fedora_prefix=fedora_prefix), name="detail"),
    ]

    if custom_patterns:
        urlpatterns.append(custom_patterns)

    if getattr(settings, 'USE_BREADCRUMBS'):
        from autobreadcrumbs.registry import breadcrumbs_registry
        from fedoralink_ui.templatetags.fedoralink_tags import rdf2lang
        import django.utils.translation
        from django.core.cache import cache

        def breadcrumb_detail(request, crumb):
            # print(request, crumb.path, crumb.name, crumb.title, crumb.view_args, crumb.view_kwargs)
            id = crumb.view_kwargs['id']
            lang = django.utils.translation.get_language()
            return get_title(id, lang)

        def get_title(id, lang):
            def _get_title():
                try:
                    return rdf2lang(FedoraObject.objects.get(pk=id).title, lang=lang)
                except:
                    import traceback
                    traceback.print_exc()
                    return None
            return cache.get_or_set('title__%s__%s' % (id, lang), _get_title, 3600)

        breadcrumbs_registry.update({
            '%s:detail' % app_name: breadcrumb_detail,
        })

    return [
        url(r'^', include(urlpatterns, namespace=app_name, app_name=app_name))
    ]


def cache_breadcrumbs(obj):
    if getattr(settings, 'USE_BREADCRUMBS'):
        from django.core.cache import cache
        from fedoralink_ui.templatetags.fedoralink_tags import rdf2lang
        import django.utils.translation

        lang = django.utils.translation.get_language()

        if cache.get('title__%s/__%s' % (obj.local_id, lang)):
            return

        local_id = obj.local_id
        prefix = obj.id[:-len(local_id)]
        ids = local_id.split('/')
        ids = [
            prefix + '/'.join(ids[:k]) for k in range(1, len(ids)+1)
        ]
        for found_obj in DCObject.objects.filter(pk__in=ids):
            cache.set('title__%s/__%s' % (found_obj.local_id, lang),
                      rdf2lang(found_obj.title, lang=lang), 3600)



