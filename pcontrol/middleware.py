# pcontrol/middleware.py
import zoneinfo
from django.utils import timezone


class TimezoneMiddleware:
    """
    Middleware для установки временной зоны на основе TIME_ZONE из настроек.
    
    Активирует timezone при каждом запросе, чтобы Django правильно конвертировал
    даты из UTC (в базе) в локальное время (Europe/Moscow) при отображении.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            tzname = 'Europe/Moscow'
            timezone.activate(zoneinfo.ZoneInfo(tzname))
        except zoneinfo.ZoneInfoNotFoundError:
            timezone.deactivate()
        
        response = self.get_response(request)
        
        return response
