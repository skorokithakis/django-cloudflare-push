#!/usr/bin/env python

import sys
from django_cloudflare_push import __version__
assert sys.version >= '2.7', "Requires Python v2.7 or above."
from distutils.core import setup
from setuptools import find_packages

setup(
    name="django-cloudflare-push",
    version=__version__,
    author="Stavros Korokithakis",
    author_email="hi@stavros.io",
    url="https://github.com/skorokithakis/django-cloudflare-push",
    description="""An piece of middleware that tells CloudFlare to HTTP/2 Push static files in a page to the client.""",
    long_description="A piece of middleware that lists all the static media in a Django page and adds a header that instructs"
                     " CloudFlare to use HTTP/2's Push functionality to send the media to the client before the latter requests them.",
    license="BSD",
    keywords="django, cloudflare, http2, push",
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
)
