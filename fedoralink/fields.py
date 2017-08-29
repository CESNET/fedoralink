import json
import logging

from django.core import exceptions
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db.models import TextField, Field, ForeignKey
from django.utils.functional import SimpleLazyObject
from django.utils.translation import ugettext_lazy as _, ungettext_lazy, string_concat

from fedoralink.fedora_meta import FedoraFieldOptions
from fedoralink.utils import value_to_rdf_literal

log = logging.getLogger('fedoralink.fields')


# helper classes copied from postgres
class AttributeSetter(object):
    def __init__(self, name, value):
        setattr(self, name, value)


class ArrayMaxLengthValidator(MaxLengthValidator):
    message = ungettext_lazy(
        'List contains %(show_value)d item, it should contain no more than %(limit_value)d.',
        'List contains %(show_value)d items, it should contain no more than %(limit_value)d.',
        'limit_value')


def prefix_validation_error(error, prefix, code, params):
    """
    Prefix a validation error message while maintaining the existing
    validation data structure.
    """
    if error.error_list == [error]:
        error_params = error.params or {}
        return ValidationError(
            # We can't simply concatenate messages since they might require
            # their associated parameters to be expressed correctly which
            # is not something `string_concat` does. For example, proxied
            # ungettext calls require a count parameter and are converted
            # to an empty string if they are missing it.
            message=string_concat(
                SimpleLazyObject(lambda: prefix % params),
                SimpleLazyObject(lambda: error.message % error_params),
            ),
            code=code,
            params=dict(error_params, **params),
        )
    return ValidationError([
        prefix_validation_error(e, prefix, code, params) for e in error.error_list
    ])


class GenericFedoraField(TextField):
    def __init__(self, model, rdf_name):
        super().__init__(null=True, blank=True)
        self.set_attributes_from_name(rdf_name)
        self.model = model
        self.fedora_options = FedoraFieldOptions(field=self, rdf_name=rdf_name)


#
# Field with fedora metadata, can be used to wrap fields on models stored in Fedora
#
class FedoraField(Field):
    empty_strings_allowed = False
    default_error_messages = {
        'item_invalid': _('Item %(nth)s in the array did not validate: '),
    }

    ANY = 100000

    def __init__(self, base_field, multiplicity=1,
                 rdf_namespace=None, rdf_name=None,
                 **kwargs):
        self.fedora_options = FedoraFieldOptions(field=self, rdf_namespace=rdf_namespace, rdf_name=rdf_name)
        if isinstance(base_field, Field):
            self.base_field = base_field
        else:
            self.base_field = base_field(**kwargs)
        self.size = multiplicity
        self.is_array = multiplicity > 1
        if self.is_array:
            self.default_validators = self.default_validators[:]
            self.default_validators.append(ArrayMaxLengthValidator(self.size))

        super().__init__(**kwargs)

    def deconstruct(self):
        """
        Called when django needs to convert an instance of the field into the arguments for the constructor
            :return name     the name of this class
            :return path     full module path of this class
            :return args     positional arguments for passing to the constructor of this class
            :return kwargs   keyword arguments for passing to the constructor of this class
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs.update({
            'base_field': self.base_field,
            'multiplicity': self.size,
            'rdf_namespace': str(self.fedora_options.rdf_namespace),
            'rdf_name': str(self.fedora_options.rdf_name)
        })
        return name, path, args, kwargs

    description = _('Field of FedoraObject of type %(base_field)s')

    def db_type(self, connection):
        if self.is_array:
            size = self.size or ''
            return 'rdf[%s[%s]]' % (self.base_field.db_type(connection), size)
        else:
            return 'rdf[%s]' % self.base_field.db_type(connection)

    def rel_db_type(self, connection):
        return 'string'

    @property
    def model(self):
        try:
            return self.__dict__['model']
        except KeyError:
            raise AttributeError("'%s' object has no attribute 'model'" % self.__class__.__name__)

    @model.setter
    def model(self, model):
        self.__dict__['model'] = model
        self.base_field.model = model

    def from_db_value(self, value, expression, connection, context):
        # called when data are loaded from the database. It is an array of RDF triplets
        # if empty, return an empty array or nothing
        if value is None:
            if self.is_array:
                return []
            return value

        if isinstance(self.base_field, ForeignKey):
            # TODO: change this to use a similar approach as ForwardManyToOneDescriptor
            target_cls = self.base_field.related_model
            value = [
                target_cls.objects.get(fedora_id=x) for x in value
            ]
        else:
            # deserialize array items
            base_from_db_value = getattr(self.base_field, 'from_db_value', None)
            if base_from_db_value:
                value = [
                    self.base_field.from_db_value(x.object, expression, connection, context) for x in value
                ]
            else:
                value = [
                    x.value for x in value
                ]

        # if we can return multiple values, return them
        if self.is_array:
            return value

        # returning single value - check if there are more than one, if so raise error
        if len(value) > 1:
            raise ValidationError('Only one value is expected but the repository returned more: %s' % value)

        # if the array is empty, return None
        if not len(value):
            return None

        # otherwise return the only value in the array
        return value[0]

    def to_python(self, value):
        if value is None:
            return value

        if isinstance(value, str):
            # if it comes from value_to_string, deserialize it
            try:
                parsed_value = json.loads(value)
                if getattr(parsed_value, '_type') == 'FedoraField':
                    return [
                        self.base_field.to_python(val) for val in getattr(parsed_value, '_data', [])
                    ]
            except:
                pass

        if self.is_array:
            return [
                self.base_field.to_python(val) for val in value
            ]
        else:
            return self.base_field.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        # return an array of RDF triplets
        if value is None:
            return []

        if not self.is_array or not(type(value) is list or type(value) is tuple or type(value) is set):
            value = [value]

        if isinstance(self.base_field, ForeignKey):
            # convert foreign key to its id and call the foreign key
            value = [i.fedora_id for i in value]
        else:
            value = [self.base_field.get_db_prep_value(i, connection, prepared=False) for i in value]
        value = [
            value_to_rdf_literal(x)
                for x in value
        ]
        return value

    def formfield(self, **kwargs):
        # TODO: use custom field & widget
        if self.is_array:
            log.error('Custom field is not implemented for arrays yet')
            return self.base_field.formfield(**kwargs)
        else:
            return self.base_field.formfield(**kwargs)

    def value_to_string(self, obj):
        "Used by django serializer"
        value = self.value_from_object(obj)

        if value is None:
            return None

        if not self.is_array:
            value = [value]

        return json.dumps({
            '_type': 'FedoraField',
            '_data': [
                self.base_field.value_to_string(AttributeSetter(self.name, val)) for val in value
            ]
        })

    def set_attributes_from_name(self, name):
        super().set_attributes_from_name(name)
        self.base_field.set_attributes_from_name(name)

    def validate(self, value, model_instance):
        if self.is_array:
            super().validate(value, model_instance)
            for index, part in enumerate(value):
                try:
                    self.base_field.validate(part, model_instance)
                except exceptions.ValidationError as error:
                    raise prefix_validation_error(
                        error,
                        prefix=self.error_messages['item_invalid'],
                        code='item_invalid',
                        params={'nth': index},
                    )
        else:
            return self.base_field.validate(value, model_instance)

    def run_validators(self, value):
        if self.is_array:
            super().run_validators(value)
            for index, part in enumerate(value):
                try:
                    self.base_field.run_validators(part)
                except exceptions.ValidationError as error:
                    raise prefix_validation_error(
                        error,
                        prefix=self.error_messages['item_invalid'],
                        code='item_invalid',
                        params={'nth': index},
                    )
        else:
            self.base_field.run_validators(value)
