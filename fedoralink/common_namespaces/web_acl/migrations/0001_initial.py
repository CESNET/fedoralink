# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-29 09:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import fedoralink.fields
import fedoralink.migration_ops
import fedoralink.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        fedoralink.migration_ops.FedoraCreateModel(
            name='Authorization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent', fedoralink.fields.FedoraField(base_field=models.CharField(max_length=512, null=True, verbose_name='People allowed to access a resource'), multiplicity=100000, rdf_name='http://www.w3.org/ns/auth/acl#agent', rdf_namespace='http://www.w3.org/ns/auth/acl#')),
                ('agent_class', fedoralink.fields.FedoraField(base_field=models.CharField(max_length=512, null=True, verbose_name='Groups of people allowed to access a resource'), multiplicity=100000, rdf_name='http://www.w3.org/ns/auth/acl#agent_class', rdf_namespace='http://www.w3.org/ns/auth/acl#')),
                ('mode', fedoralink.fields.FedoraField(base_field=models.CharField(choices=[('http://www.w3.org/ns/auth/acl#Read', 'Read'), ('http://www.w3.org/ns/auth/acl#Write', 'Write')], max_length=512, verbose_name='Resource access mode, either acl:Read or acl:Write'), multiplicity=100000, rdf_name='http://www.w3.org/ns/auth/acl#mode', rdf_namespace='http://www.w3.org/ns/auth/acl#')),
                ('access_to', fedoralink.fields.FedoraField(base_field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='fedoralink.FedoraObject', verbose_name='Resource to which this object applies'), multiplicity=100000, rdf_name='http://www.w3.org/ns/auth/acl#access_to', rdf_namespace='http://www.w3.org/ns/auth/acl#')),
                ('access_to_class', fedoralink.fields.FedoraField(base_field=models.CharField(max_length=512, verbose_name='RDF class of resources to which this authorization applies'), multiplicity=100000, rdf_name='http://www.w3.org/ns/auth/acl#access_to_class', rdf_namespace='http://www.w3.org/ns/auth/acl#')),
                ('fedora_id', fedoralink.models.FedoraResourceUrlField(blank=True, null=True, unique=True, verbose_name='Fedora resource URL')),
            ],
            fedora_options={'default_parent': 'web_acl_authorization', 'field_options': None, 'primary_rdf_type': 'http://www.w3.org/ns/auth/acl#Authorization', 'rdf_namespace': 'http://www.w3.org/ns/auth/acl#', 'rdf_types': ['http://www.w3.org/ns/auth/acl#Authorization']},
        ),
    ]
