# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-23 13:11
from __future__ import unicode_literals

from django.db import migrations, models
import fedoralink.migration_ops
import fedoralink.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        fedoralink.migration_ops.FedoraCreateModel(
            name='DCObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(default='', verbose_name='Title')),
                ('creator', models.TextField(default='', verbose_name='Creator')),
                ('subject', models.CharField(default='', max_length=255, verbose_name='Subject')),
                ('description', models.TextField(default='', verbose_name='Description')),
                ('publisher', models.CharField(default='', max_length=255, verbose_name='Publisher')),
                ('contributor', models.CharField(default='', max_length=255, verbose_name='Contributor')),
                ('date', models.CharField(default='', max_length=128, verbose_name='Date')),
                ('type', models.CharField(choices=[('Collection', 'Collection'), ('Dataset', 'Dataset'), ('Event', 'Event'), ('Image', 'Image'), ('InteractiveResource', 'InteractiveResource'), ('Service', 'Service'), ('Software', 'Software'), ('Sound', 'Sound'), ('Text', 'Text'), ('PhysicalObject', 'PhysicalObject')], default='Text', max_length=20, verbose_name='Type')),
                ('identifier', models.CharField(default='', max_length=255, verbose_name='Identifier')),
                ('source', models.CharField(max_length=255, verbose_name='Source')),
                ('language', models.CharField(max_length=128, verbose_name='Language')),
                ('relation', models.TextField(default='', verbose_name='Relation')),
                ('coverage', models.CharField(default='', max_length=255, verbose_name='Coverage')),
                ('rights', models.TextField(default='', verbose_name='Rights')),
                ('abstract', models.TextField(default='', verbose_name='Abstract')),
                ('accessRights', models.CharField(default='', max_length=255)),
                ('accrualMethod', models.CharField(default='', max_length=255)),
                ('accrualPeriodicity', models.CharField(default='', max_length=128)),
                ('accrualPolicy', models.CharField(default='', max_length=255)),
                ('alternative', models.TextField(default='', verbose_name='Alternative')),
                ('audience', models.CharField(default='', max_length=255, verbose_name='Audience')),
                ('available', models.CharField(default='', max_length=128, verbose_name='Available')),
                ('bibliographicCitation', models.TextField(default='', verbose_name='Bibliography')),
                ('conformsTo', models.CharField(default='', max_length=255)),
                ('created', models.CharField(default='', max_length=128, verbose_name='Created')),
                ('dateAccepted', models.CharField(default='', max_length=128, verbose_name='Accepted')),
                ('dateCopyrighted', models.CharField(default='', max_length=128, verbose_name='Copyrighted')),
                ('dateSubmitted', models.CharField(default='', max_length=128, verbose_name='Submitted')),
                ('educationLevel', models.CharField(default='', max_length=225, verbose_name='Submitted')),
                ('extent', models.CharField(default='', max_length=225, verbose_name='Extent')),
                ('dformat', models.CharField(default='', max_length=225, verbose_name='Format')),
                ('hasFormat', models.CharField(default='', max_length=225)),
                ('hasPart', models.CharField(default='', max_length=225)),
                ('hasVersion', models.CharField(default='', max_length=225)),
                ('instructionalMethod', models.TextField(default='')),
                ('isFormatOf', models.CharField(default='', max_length=225)),
                ('isPartOf', models.CharField(default='', max_length=225)),
                ('isReferencedBy', models.CharField(default='', max_length=225)),
                ('isReplacedBy', models.CharField(default='', max_length=225)),
                ('isRequiredBy', models.CharField(default='', max_length=225)),
                ('issued', models.CharField(default='', max_length=128, verbose_name='Issued')),
                ('isVersionOf', models.CharField(default='', max_length=225)),
                ('license', models.TextField(default='', verbose_name='License')),
                ('mediator', models.CharField(default='', max_length=255, verbose_name='Mediator')),
                ('medium', models.CharField(default='', max_length=255, verbose_name='Medium')),
                ('modified', models.CharField(default='', max_length=128, verbose_name='Issued')),
                ('provenance', models.TextField(default='', verbose_name='Provenance')),
                ('references', models.CharField(default='', max_length=255, verbose_name='References')),
                ('replaces', models.CharField(default='', max_length=225)),
                ('requires', models.CharField(default='', max_length=225)),
                ('rightsHolder', models.CharField(default='', max_length=225)),
                ('spatial', models.TextField(default='', verbose_name='Spatial')),
                ('tableOfContents', models.TextField(default='', verbose_name='TableOfContents')),
                ('temporal', models.TextField(default='', verbose_name='Temporal')),
                ('valid', models.CharField(default='', max_length=128, verbose_name='Valid')),
                ('fedora_id', fedoralink.models.FedoraResourceUrlField(blank=True, null=True, verbose_name='Fedora resource URL')),
            ],
            fedora_options={'default_parent': 'dc_dcobject', 'field_options': None, 'primary_rdf_type': 'http://purl.org/dc/elements/1.1/object', 'rdf_namespace': 'http://purl.org/dc/elements/1.1/', 'rdf_types': ['http://purl.org/dc/elements/1.1/object']},
        ),
    ]
