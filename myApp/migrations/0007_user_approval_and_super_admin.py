from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def seed_super_admin_and_approve_existing_users(apps, schema_editor):
    User = apps.get_model("myApp", "User")
    now = timezone.now()

    User.objects.filter(approval_status='pending').update(
        approval_status='approved',
        approved_at=now,
    )

    super_admin, created = User.objects.get_or_create(
        username="superadmin",
        defaults={
            "email": "superadmin@Agriplus.demo",
            "role": "super_admin",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
            "approval_status": "approved",
            "approved_at": now,
            "password": make_password("demo12345"),
        },
    )

    if not created:
        updated = False
        if super_admin.role != "super_admin":
            super_admin.role = "super_admin"
            updated = True
        if super_admin.approval_status != "approved":
            super_admin.approval_status = "approved"
            updated = True
        if not super_admin.is_active:
            super_admin.is_active = True
            updated = True
        if not super_admin.is_staff:
            super_admin.is_staff = True
            updated = True
        if not super_admin.is_superuser:
            super_admin.is_superuser = True
            updated = True
        if super_admin.approved_at is None:
            super_admin.approved_at = now
            updated = True
        if updated:
            super_admin.save()


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0006_user_assigned_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='approval_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'role': 'super_admin'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_users',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('super_admin', 'Super Admin'),
                    ('admin', 'Admin'),
                    ('farmer', 'Farmer'),
                    ('technician', 'Technician'),
                ],
                default='farmer',
                max_length=20,
            ),
        ),
        migrations.RunPython(seed_super_admin_and_approve_existing_users, migrations.RunPython.noop),
    ]
