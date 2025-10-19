import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user, created = User.objects.get_or_create(username='debug_user', defaults={'email':'debug@example.com'})
if created or not user.has_usable_password():
    user.set_password('pass')
    user.save()

c = Client()
c.force_login(user)
# do a POST mimicking the inline AJAX with missing exercicios
try:
    resp = c.post('/treinos/novo/', {'nome':'debug',}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print('STATUS', resp.status_code)
    print(resp.content)
    try:
        print('JSON:', resp.json())
    except Exception:
        pass
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
