# reset_demo_passwords.py
# Quick script to reset all demo user passwords to "demo12345"
# Usage: python reset_demo_passwords.py

import os
import django

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myProject.settings")

django.setup()

from myApp.models import User

DEMO_USERS = ["admin", "tech_ana", "farmer_ben", "farmer_rosa", "farmer_carlos"]
PASSWORD = "demo12345"

print("Resetting passwords for demo users...")
for username in DEMO_USERS:
    try:
        user = User.objects.get(username=username)
        user.set_password(PASSWORD)
        user.is_active = True
        if username == "admin":
            user.is_staff = True
        user.save()
        print(f"✅ Reset password for {username}")
    except User.DoesNotExist:
        print(f"❌ User {username} not found")
    except Exception as e:
        print(f"❌ Error resetting {username}: {e}")

print("\n✅ Password reset complete!")
print(f"All demo users now have password: {PASSWORD}")

