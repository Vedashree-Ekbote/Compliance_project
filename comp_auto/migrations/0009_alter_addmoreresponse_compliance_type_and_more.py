# Generated by Django 4.1.7 on 2023-12-30 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comp_auto', '0008_rename_summary_addmoreresponse_summary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addmoreresponse',
            name='compliance_type',
            field=models.CharField(choices=[('compliant', 'Compliant'), ('partially-compliant', 'Partially Compliant'), ('non-compliant', 'Non-Compliant'), ('not-applicable', 'Not-applicable')], max_length=20),
        ),
        migrations.AlterField(
            model_name='userresponse',
            name='compliance_type',
            field=models.CharField(choices=[('compliant', 'Compliant'), ('partially-compliant', 'Partially Compliant'), ('non-compliant', 'Non-Compliant'), ('not-applicable', 'Not-applicable')], max_length=20),
        ),
    ]
