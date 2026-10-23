from django.db import migrations


def disable_forced_password_change(apps, schema_editor):
    Supplier = apps.get_model('suppliers', 'Supplier')
    Supplier.objects.update(must_change_password=False)


class Migration(migrations.Migration):
    dependencies = [
        ('suppliers', '0005_set_initial_supplier_passwords'),
    ]

    operations = [
        migrations.RunPython(disable_forced_password_change, migrations.RunPython.noop),
    ]
