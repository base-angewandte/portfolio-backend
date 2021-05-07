import shortuuid

from django.db import models


class AbstractBaseModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_changed = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ('-date_created',)


# Based on implementation from https://github.com/nebstrebor/django-shortuuidfield
class ShortUUIDField(models.CharField):
    """A field which stores a Short UUID value in base57 format.

    This may also have the Boolean attribute 'auto' which will set the
    value on initial save to a new UUID value (calculated using
    shortuuid). Note that while all UUIDs are expected to be unique we
    enforce this with a DB constraint.
    """

    def __init__(self, auto=True, prefix=None, namespace=None, *args, **kwargs):
        self.auto = auto
        self.prefix = prefix
        self.namespace = namespace
        # We store UUIDs in base57 format, which is fixed at 22 characters.
        # If we want a prefix, we need to increase the characters size.
        max_length = 22
        if prefix:
            max_length += 1 + len(prefix)
        kwargs['max_length'] = max_length
        if auto:
            # Do not let the user edit UUIDs if they are auto-assigned.
            kwargs['editable'] = False
            kwargs['blank'] = True
            kwargs['unique'] = True

        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        if self.prefix:
            kwargs['prefix'] = self.prefix
        if self.auto:
            del kwargs['editable']
            del kwargs['blank']
            del kwargs['unique']
        else:
            kwargs['auto'] = self.auto
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        """This is used to ensure that we auto-set values if required.

        See CharField.pre_save
        """
        value = super().pre_save(model_instance, add)
        if self.auto and not value:
            # Assign a new value for this attribute if required.
            value = shortuuid.uuid(name=self.namespace)
            if self.prefix:
                value = self.prefix + ':' + value
            setattr(model_instance, self.attname, value)
        return value

    def formfield(self, **kwargs):
        if self.auto:
            return None
        return super().formfield(**kwargs)
