"""Empty migration to alter ReportTemplate.output_formats to match models.

This migration restores the missing migration referenced by 0003_aianalysis.
It sets the `output_formats` field on ReportTemplate to a JSONField with default=list,
matching the current model state.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reporttemplate",
            name="output_formats",
            field=models.JSONField(default=list),
        ),
    ]
