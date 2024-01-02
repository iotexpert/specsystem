import datetime
from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone
import logging
logger = logging.getLogger('response')

class TimeStampMiddleware(object):
    """Middleware class add message timestamp to request
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, '_req_dt'):
            dt = timezone.now()
            request._req_dt = dt

        try:
            resp = self.get_response(request)
        finally:
            if hasattr(request, "user") and hasattr(request.user, "username") and request.user.username:
                user = request.user.username
            else:
                user = "anonymous"
            log_msg = f'{request.method} {request.build_absolute_uri()} {user}'
            log_msg += f' {(timezone.now() - dt).total_seconds()} {resp.status_code} {resp.headers["content-length"] if "content-length" in resp.headers else ""}'
            if "HTTP_REFERER" in request.environ: #pragma nocover
                log_msg += f' {request.environ["HTTP_REFERER"]}'
            logger.info(log_msg)
            if resp.status_code == 400:
                logger.debug(resp.content.decode())

        return resp

class SessionTimeoutMiddleware(object):
    """Middleware class timeout session after inactivity
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # timeout idle sessions
        if  hasattr(request, "user") and request.user.is_authenticated:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            last_activity = request.session.get('last_activity', None)
            if last_activity:
                last_activity = datetime.datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
                if (datetime.datetime.now() - last_activity).seconds > settings.SESSION_IDLE_TIMEOUT:
                    logout(request)
            request.session['last_activity'] = current_time
        response = self.get_response(request)
        return response
