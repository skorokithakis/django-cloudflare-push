django-cloudflare-push
======================

About
-----

django-cloudflare-push is a small piece of middleware that looks at the list of
static files in each page that is requested (you need to be using some sort of
static files processor, like Django's built-in one), and [adds a Link
header](https://www.cloudflare.com/website-optimization/http2/serverpush/) that
CloudFlare uses to push the static files to the browser before the latter
requests them, using HTTP/2 Push.

[![PyPI version](https://img.shields.io/pypi/v/django-cloudflare-push.svg)](https://pypi.python.org/pypi/django-cloudflare-push)



Installing django-cloudflare-push
---------------------------------

* Install django-cloudflare-push using pip: `pip install django-cloudflare-push`

* Add tokenauth to your authentication backends:

```python
MIDDLEWARE = (
    'django_cloudflare_push.middleware.push_middleware',
    ...
)
```

Done! Your static media will be pushed. You can test the middleware by looking
for the `Link` header.


License
-------

This software is distributed under the BSD license.
