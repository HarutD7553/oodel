from django.db import connection
from django.http import JsonResponse


def health(request):
    """Report whether both Django and its configured database are available."""
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()

    return JsonResponse({'status': 'ok', 'database': 'ok'})
