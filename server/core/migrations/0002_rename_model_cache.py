from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Model_cache",
            new_name="ModelCache",
        ),
        migrations.AlterModelTable(
            name="ModelCache",
            table="core_model_cache",
        ),
        migrations.RenameField(
            model_name="ModelCache",
            old_name="sessHash",
            new_name="session_hash",
        ),
        migrations.AlterField(
            model_name="ModelCache",
            name="blocked",
            field=models.BooleanField(default=True),
        ),
    ]
