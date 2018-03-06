"""Parse a page and add a Link header to the request, which CloudFlare can use to push static media to an HTTP/2 client."""

from django.conf import settings
from django.contrib.staticfiles import storage
from django.contrib.staticfiles.templatetags import staticfiles
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject


DEFAULT_EXTENSION_ORDERING = ['css', 'js', '*']
ACCEPTED_EXTENSIONS = getattr(settings, 'CLOUDFLARE_PUSH_EXTENSIONS', DEFAULT_EXTENSION_ORDERING)


class FileCollector(object):
    def __init__(self):
        self.collection = []

    def collect(self, path):
        if not path.endswith('/'):
            if '*' not in ACCEPTED_EXTENSIONS:
                ext = path.rsplit(".")[-1]
                if ext not in ACCEPTED_EXTENSIONS:
                    return
            self.collection.append(path)


def storage_factory(collector):
    class DebugConfiguredStorage(LazyObject):
        def _setup(self):
            configured_storage_cls = get_storage_class(settings.STATICFILES_STORAGE)

            class DebugStaticFilesStorage(configured_storage_cls):

                def __init__(self, collector, *args, **kwargs):
                    super(DebugStaticFilesStorage, self).__init__(*args, **kwargs)
                    self.collector = collector

                def url(self, path):
                    self.collector.collect(path)
                    return super(DebugStaticFilesStorage, self).url(path)

            self._wrapped = DebugStaticFilesStorage(collector)
    return DebugConfiguredStorage


def sort_urls(urls):
    """
    Order URLs by extension, according to the order of the list ACCEPTED_EXTENSIONS.
    """
    def sorter(x):
        ext = x.rsplit(".")[-1]
        lookup = ext if ext in ACCEPTED_EXTENSIONS else '*'
        if lookup in ACCEPTED_EXTENSIONS:
            return ACCEPTED_EXTENSIONS.index(lookup)
        # simple fallback
        return len(ACCEPTED_EXTENSIONS)
    urls.sort(key=sorter)
    return urls


def push_middleware(get_response):
    def middleware(request):
        collector = FileCollector()
        storage.staticfiles_storage = staticfiles.staticfiles_storage = storage_factory(collector)()
        response = get_response(request)
        collection_copy = list(collector.collection)  # For compatibility with 2.7.
        urls = list(set(storage.staticfiles_storage.url(f) for f in collection_copy))
        urls = sort_urls(urls)
        response["Link"] = ", ".join(["<%s>; rel=preload" % url for url in urls[:10]])
        return response
    return middleware
