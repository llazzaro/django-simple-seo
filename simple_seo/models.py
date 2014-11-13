from django.db import models

from simple_seo.fields import (
    TitleTagField,
    KeywordsTagField,
    MetaTagField,
    ImageMetaTagField,
    URLMetaTagField,
    BaseTagField)


def _post_init_field_populate(sender, instance, *args, **kwargs):
    """
    Must populate the fields with 'populate_from' value
    Only populates if destination field has empty values
    Saves values, so every populating are only save to database once
    (first time)
    """
    for field in instance._meta.fields:
        _populate_from_name = getattr(field, 'populate_from', None)
        if _populate_from_name and (
            isinstance(
                field,
                (BaseTagField, URLMetaTagField, ImageMetaTagField)
            ) or
            issubclass(
                field.__class__,
                (BaseTagField, URLMetaTagField, ImageMetaTagField)
        )):
            _populate_from_tag = getattr(instance, _populate_from_name, None)
            if _populate_from_tag:
                # Populates meta_content and tag_value values to the
                # destination field
                # Case1: we populate always tag_value if not self_closed in
                #        both fields
                # Case2: both are metas self_closed, then copy meta_content
                # Case3: destination is a meta self_closed but origin field is
                #        not self_closed: copy tag_value
                destination_tag = getattr(instance, field.name, None)
                if destination_tag is not None:
                    if destination_tag.meta_content is None or (
                        destination_tag.meta_content == ''
                    ):
                        if destination_tag.self_closed and _populate_from_tag.self_closed:
                            destination_tag.meta_content = _populate_from_tag.meta_content
                            setattr(instance, field.name, destination_tag)
                            instance.save()
                        if destination_tag.self_closed and not _populate_from_tag.self_closed:
                            destination_tag.meta_content = _populate_from_tag.tag_value
                            setattr(instance, field.name, destination_tag)
                            instance.save()

                    if destination_tag.tag_value is None or destination_tag.tag_value == '':
                        if not destination_tag.self_closed and not _populate_from_tag.self_closed:
                            destination_tag.tag_value = _populate_from_tag.tag_value
                            setattr(instance, field.name, destination_tag)
                            instance.save()


class BaseMetadata(models.Model):
    """
    Abstract Base Metadata Class
    """
    view_name = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(BaseMetadata, self).__init__(*args, **kwargs)
        models.signals.post_init.connect(
            _post_init_field_populate, sender=self.__class__
        )

    def __unicode__(self):
        return '{0} - {1}'.format(self.view_name, self.content_type)


class SimpleMetadataMixin(models.Model):
    """
    Mixin to include usual metadata tags.
    """
    title = TitleTagField(null=True, blank=True)
    keywords = KeywordsTagField(null=True, blank=True)
    description = MetaTagField(null=True, blank=True)
    author = MetaTagField(null=True, blank=True)

    class Meta:
        abstract = True


class OpenGraphMetadataMixin(models.Model):
    """
    Mixin to include OpenGraph metadata tags.
    """
    og_title = MetaTagField(
        name='og:title',
        max_length=95,
        null=True,
        blank=True,
        populate_from='title'
    )
    og_type = MetaTagField(
        name='og:type',
        max_length=15,
        null=True,
        blank=True
    )
    og_image = ImageMetaTagField(
        name='og:image',
        upload_to='seo/images/',
        null=True,
        blank=True
    )
    og_url = URLMetaTagField(name='og:url', null=True, blank=True)
    og_description = MetaTagField(
        name='og:description',
        max_length=297,
        null=True,
        blank=True,
        populate_from='description'
    )
    og_admins = MetaTagField(
        name='og:admins',
        max_length=297,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class TwitterMetadataMixin(models.Model):
    """
    Mixin to include Twitter metadata tags.
    """
    twitter_title = MetaTagField(
        name='twitter:title',
        max_length=70,
        null=True,
        blank=True,
        populate_from='og:title'
    )
    twitter_card = MetaTagField(
        name='twitter:card',
        max_length=15,
        null=True,
        blank=True
    )
    twitter_image = ImageMetaTagField(
        name='twitter:image',
        upload_to='seo/images/',
        null=True, blank=True,
        populate_from='og:image'
    )
    twitter_description = MetaTagField(
        name='twitter:description',
        max_length=200,
        null=True,
        blank=True,
        populate_from='og:description'
    )

    class Meta:
        abstract = True


try:
    # In case South is installed
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules(
        [],
        [
            "^simple_seo\.fields\.TitleTagField",
            "^simple_seo\.fields\.MetaTagField",
            "^simple_seo\.fields\.URLMetaTagField",
            "^simple_seo\.fields\.ImageMetaTagField",
            "^simple_seo\.fields\.KeywordsTagField",
        ]
    )
except ImportError:
    pass


# Just for testing purposes...
class TestMetadata(BaseMetadata, SimpleMetadataMixin, OpenGraphMetadataMixin,
                   TwitterMetadataMixin):
    """
    My Seo Model
    """
    pass
