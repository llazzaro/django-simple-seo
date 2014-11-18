from django import template
from django.core.urlresolvers import resolve
from django.core.cache import cache
from django.utils import translation
from django.conf import settings
from django.contrib.contenttypes import models as contenttypes
import logging
from .. import get_class_for_view

from ..settings import (
    SEO_CACHE_PREFIX,
    SEO_CACHE_TIMEOUT,
    SEO_USE_CACHE,
)

from ..fields import (
    TitleTagField,
    MetaTagField,
    KeywordsTagField,
    URLMetaTagField,
    ImageMetaTagField
)


log = logging.getLogger(__name__)

register = template.Library()


class MetadataNode(template.Node):
    """
    Template Tag node for Metadata
    * gets the view name from request
    * obtains metadata model and object
    * print each supported field
    """

    @staticmethod
    def _build_prefix(context, view_name, content_type):
        lang = translation.get_language()
        return '{0}:{1}:{2}:{3}:{4}'.format(
            SEO_CACHE_PREFIX, view_name, content_type, lang,
            context['request'].path
        )

    @staticmethod
    def _check_field_i18n(field):
        """
        Avoid fields that has _XX lang prefix
        """
        if not getattr(settings, 'USE_I18N', None) or field is None:
            return False
        for lang in settings.LANGUAGES:
            if '_'+lang[0] in field.name:
                return True

        return False

    def __init__(self, instance=None):
        self.instance = template.Variable(instance) if instance else None

    def render(self, context):
        metadata_html = None
        content_type = None
        instance = None

        # resolve view name
        view_name = resolve(context['request'].path).url_name

        # resolve content type for the model
        if self.instance:
            instance = self.instance.resolve(context)
            content_type = contenttypes.ContentType.objects.get_for_model(
                type(instance)
            )

        # Check if metadata is in cache
        if SEO_USE_CACHE:
            metadata_html = cache.get(
                self._build_prefix(context, view_name, content_type)
            )

        if not metadata_html:
            seo_model = get_class_for_view(view_name)

            # default metadata
            try:
                default_metadata = seo_model.objects.get(
                    view_name='', content_type__isnull=True
                )
            except seo_model.DoesNotExist:
                default_metadata = None

            # specific metadata
            metadatas = seo_model.objects.filter(view_name=view_name)

            if content_type:
                metadatas = metadatas.filter(content_type=content_type)

            if len(metadatas):
                # use the first of the found metadatas
                metadata = metadatas[0]
            else:
                # or the default one if nothing is found
                metadata = default_metadata
                default_metadata = None

            # generate html
            metadata_html = ''

            if metadata:
                # put the current instance as the context for the tag
                tag_context = template.Context({'object': instance})

                for field in metadata._meta.fields:
                    if not self._check_field_i18n(field) and isinstance(
                        field,
                        (
                            TitleTagField,
                            MetaTagField,
                            KeywordsTagField,
                            URLMetaTagField,
                            ImageMetaTagField
                        )
                    ):
                        if default_metadata:
                            # add the default value to the context
                            tag_context['default'] = str(
                                field.to_python(
                                    getattr(default_metadata, field.name)
                                )
                            )
                            print 'default', tag_context['default']

                        # print the tag
                        printed_tag = field.to_python(
                            getattr(metadata, field.name)
                        ).print_tag(tag_context)

                        if printed_tag:
                            metadata_html += printed_tag + '\n'
                    else:
                        pass

                if metadata_html != '' and SEO_USE_CACHE:
                    cache.set(
                        self._build_prefix(context, view_name),
                        metadata_html,
                        SEO_CACHE_TIMEOUT
                    )

        return metadata_html or ''


@register.tag
def metadata(parser, token):
    args = token.split_contents()[1:]

    return MetadataNode(args[0] if len(args) else None)
