from __future__ import print_function
from django import forms
from django.conf import urls as url_conf
from django.core import urlresolvers
from django.forms import models as model_forms
from django.views import generic as generic_views
from django.contrib.admin import ModelAdmin
from functools import update_wrapper, partial
from . import load_view_names


class BaseMetadataForm(forms.ModelForm):
    view_name = forms.ChoiceField(choices=load_view_names(), required=False)


class DefaultMetadataUpdateView(generic_views.UpdateView):
    template_name = 'admin/simple_seo/default.html'

    def get_context_data(self, **kwargs):
        context = super(DefaultMetadataUpdateView, self).get_context_data(
            **kwargs
        )
        context.update(self.kwargs)
        return context

    def get_object(self):
        return self.model.objects.get_default()

    def get_form_class(self):
        return model_forms.modelform_factory(
            self.model,
            exclude=('view_name', 'content_type'),
            formfield_callback=self.kwargs['formfield_callback'],
        )

    def get_success_url(self):
        info = self.model._meta.app_label, self.model._meta.module_name

        if self.request.POST.get('_continue', False):
            success_url = urlresolvers.reverse(
                'admin:{0}_{1}_default'.format(*info)
            )
        else:
            success_url = urlresolvers.reverse(
                'admin:{0}_{1}_changelist'.format(*info)
            )

        return success_url


class BaseMetadataAdmin(ModelAdmin):
    """
    Overrides default admin to add autodiscovered views into a choice field
    """
    list_display = ['view_name', 'content_type']
    exclude = []
    form = BaseMetadataForm
    change_list_template = 'admin/simple_seo/change_list.html'

    def __init__(self, *args, **kwargs):
        super(BaseMetadataAdmin, self).__init__(*args, **kwargs)
        self.default_metadata_view = DefaultMetadataUpdateView.as_view(
            model=self.model
        )

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(BaseMetadataAdmin, self).formfield_for_dbfield(
            db_field,
            **kwargs
        )
        if db_field.name == 'title':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        if db_field.name == 'description':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        if db_field.name == 'keywords':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        if db_field.name == 'og:title':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        if db_field.name == 'og:description':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        if db_field.name == 'twitter:title':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        if db_field.name == 'twitter:description':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        return formfield

    def queryset(self, request):
        queryset = super(BaseMetadataAdmin, self).queryset(request)
        queryset = queryset.exclude(
            view_name__isnull=True,
            content_type__isnull=True
        )

        return queryset

    def get_urls(self):
        urls = super(BaseMetadataAdmin, self).get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        extra_urls = url_conf.patterns(
            '',
            url_conf.url(
                r'^default/$',
                wrap(self.default_metadata),
                name='{0}_{1}_default'.format(*info)
            ),
        )

        return extra_urls + urls

    def default_metadata(self, request):
        return self.default_metadata_view(
            request,
            title='Default Metadata',
            opts=self.model._meta,
            formfield_callback=partial(
                self.formfield_for_dbfield,
                request=request
            ),
        )
