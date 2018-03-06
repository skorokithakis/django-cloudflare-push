"""Parse a page and add a Link header to the request, which CloudFlare can use to push static media to an HTTP/2 client."""

from django.conf import settings
from django.contrib.staticfiles import storage
from django.contrib.staticfiles.templatetags import staticfiles
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject


FILE_FILTER = getattr(settings, 'CLOUDFLARE_PUSH_FILTER', lambda x: True)


class FileCollector(object):
    def __init__(self):
        self.collection = []

    def collect(self, path):
        if not path.endswith('/') and FILE_FILTER(path.lower()):
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
    Order URLs by extension.
    This function accepts a list of URLs and orders them by their extension.
    CSS files are sorted to the start of the list, then JS, then everything
    else.
    """
    order = {"css": 0, "js": 1}
    urls.sort(key=lambda x: order.get(x.rsplit(".")[-1].lower(), 2))
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
