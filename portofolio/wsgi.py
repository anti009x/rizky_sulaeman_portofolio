import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portofolio.settings')
application = get_wsgi_application()

# Expose the WSGI callable for Vercel
app = application
