import django
django.setup()

from django.core.exceptions import ValidationError
from django.db import models, connection
from django.test import TestCase
from rdflib import Literal, XSD

from fedoralink.fields import FedoraField


class FedoraFieldTests(TestCase):

    """
    Tests single field, their construction and deconstruction and from_db_value
    """

    def test_deconstruct(self):
        fld = FedoraField(models.CharField, max_length=10, multiplicity=FedoraField.ANY)
        fld.set_attributes_from_name('a')
        self.assertIsNotNone(fld.base_field)
        self.assertIsInstance(fld.base_field, models.CharField)
        name, path, args, kwargs = fld.deconstruct()
        print(name, path, args, kwargs)
        self.assertEqual(name, 'a')
        self.assertEqual(path, 'fedoralink.fields.FedoraField')
        self.assertEqual(len(args), 0)
        self.assertEquals(kwargs['max_length'], 10)
        self.assertEquals(kwargs['rdf_namespace'], 'http://cesnet.cz/ns/repository#')
        self.assertEquals(kwargs['rdf_name'], 'http://cesnet.cz/ns/repository#a')
        self.assertEquals(kwargs['multiplicity'], FedoraField.ANY)

    def test_dbtype(self):
        fld1 = FedoraField(models.CharField, max_length=10, multiplicity=FedoraField.ANY)
        self.assertEqual(fld1.db_type(connection), 'rdf[varchar(10)[100000]]')

        fld2 = FedoraField(models.CharField, max_length=10)
        self.assertFalse(fld2.is_array)
        self.assertEqual(fld2.db_type(connection), 'rdf[varchar(10)]')

    def test_string_from_db_value(self):
        fld1 = FedoraField(models.CharField, max_length=10, multiplicity=FedoraField.ANY)
        db_value = [
            Literal('Lorem'),
            Literal('Ipsum')
        ]
        val = fld1.from_db_value(db_value, None, connection, {})
        self.assertIsInstance(val, list)
        self.assertEqual(len(val), 2)
        self.assertIs(val[0], 'Lorem')
        self.assertIs(val[1], 'Ipsum')

    def test_int_from_db_value(self):
        fld1 = FedoraField(models.IntegerField, multiplicity=FedoraField.ANY)
        db_value = [
            Literal(12),
            Literal(23)
        ]
        val = fld1.from_db_value(db_value, None, connection, {})
        self.assertIsInstance(val, list)
        self.assertEqual(len(val), 2)
        self.assertIs(val[0], 12)
        self.assertIs(val[1], 23)


    def test_single_from_db_value(self):
        fld1 = FedoraField(models.IntegerField)
        db_value = [
            Literal(12),
            Literal(23)
        ]
        try:
            val = fld1.from_db_value(db_value, None, connection, {})
            raise AssertionError('Should not pass')
        except ValidationError as e:
            self.assertEqual(e.message, 'Only one value is expected but the repository returned more: [12, 23]')

        db_value = [
            Literal(12)
        ]
        val = fld1.from_db_value(db_value, None, connection, {})
        self.assertIs(val, 12)

    def test_to_python(self):
        fld1 = FedoraField(models.CharField, max_length=10)
        self.assertEqual(fld1.to_python('1'), '1')

        fld2 = FedoraField(models.CharField, max_length=10, multiplicity=FedoraField.ANY)
        self.assertEqual(fld2.to_python(['1', '2']), ['1', '2'])

        fld3 = FedoraField(models.IntegerField)
        self.assertEqual(fld3.to_python('1'), 1)

    def test_get_db_prep_value(self):
        fld1 = FedoraField(models.CharField, max_length=10)
        val = fld1.get_db_prep_value("Lorem ipsum", connection)
        self.assertEqual(val,[
            Literal("Lorem ipsum", datatype=XSD.string)
        ])

        fld2 = FedoraField(models.CharField, max_length=10, multiplicity=FedoraField.ANY)
        val = fld2.get_db_prep_value(["Lorem", "ipsum"], connection)
        self.assertEqual(val,[
            Literal("Lorem", datatype=XSD.string),
            Literal("ipsum", datatype=XSD.string)
        ])

        fld3 = FedoraField(models.IntegerField)
        val = fld3.get_db_prep_value(12, connection)
        self.assertEqual(val,[
            Literal(12, datatype=XSD.integer)
        ])
