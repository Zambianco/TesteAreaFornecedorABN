from django.contrib.auth.hashers import make_password
from django.db import migrations


def set_initial_supplier_passwords(apps, schema_editor):
    Supplier = apps.get_model('suppliers', 'Supplier')
    for supplier in Supplier.objects.all():
        user = supplier.user
        user.password = make_password('abn@2026')
        user.save(update_fields=['password'])
        supplier.must_change_password = True
        supplier.save(update_fields=['must_change_password'])


class Migration(migrations.Migration):
    dependencies = [
        ('suppliers', '0004_remove_evaluation_score_nonnegative_and_more'),
    ]

    operations = [
        migrations.RunPython(set_initial_supplier_passwords, migrations.RunPython.noop),
    ]
