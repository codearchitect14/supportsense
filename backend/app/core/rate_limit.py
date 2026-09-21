from slowapi import Limiter
from slowapi.util import get_remote_address

# slowapi's global default_limits enforcement relies on middleware route
# introspection that does not see routes through this FastAPI version's
# router wrapping. Every route must therefore be decorated explicitly with
# @limiter.limit(settings.rate_limit_default) (or a tighter limit) rather
# than relying on the middleware to apply a default automatically.
limiter = Limiter(key_func=get_remote_address)
