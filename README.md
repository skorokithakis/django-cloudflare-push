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

Somewhat counter-intuitively, django-cloudflare-push is compatible with *any*
provider that supports HTTP/2 Push using Link headers, which is pretty much
most of them. For example, the Caddy webserver supports this with the `push`
directive, and this library will work just fine with that.

[![PyPI version](https://img.shields.io/pypi/v/django-cloudflare-push.svg)](https://pypi.python.org/pypi/django-cloudflare-push)



Installing django-cloudflare-push
---------------------------------

* Install django-cloudflare-push using pip: `pip install django-cloudflare-push`

* Add the middleware to your MIDDLEWARE setting:

```python
MIDDLEWARE = (
    'django_cloudflare_push.middleware.push_middleware',
    ...
)
```

Done! Your static media will be pushed. You can test the middleware by looking
for the `Link` header.

Settings
--------

```python
CLOUDFLARE_PUSH_FILTER = lambda file: True
```

Allows you to customize what files will be sent to the client to be preloaded.
This setting should be set to a callable, which accepts a single parameter
(the name of the file to preload). By default, `django-cloudflare-push` pushes
all static files.

For instance, to push _only_ static CSS and JavaScript files:

```python
CLOUDFLARE_PUSH_FILTER = lambda x: x.endswith('.css') or x.endswith('.js')
```

Webserver configuration
-----------------------

Here's how to configure various webservers to work well with
`django-cloudflare-push`:

### nginx

If you're running nginx v1.13.9 or later, you can just include the
`http2_push_preload on` directive in your configuration:

```
server {
    ...
    http2_push_preload on;
    ...
}
```

### Caddy

With Caddy, you can use the [`push` directive](https://caddyserver.com/docs/push):

```
push
```

...I know.

License
-------

This software is distributed under the BSD license.
