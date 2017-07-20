"""Parse a page and add a Link header to the request, which CloudFlare can use to push static media to an HTTP/2 client."""

from django.conf import settings
from django.contrib.staticfiles import storage
from django.contrib.staticfiles.templatetags import staticfiles
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject


class FileCollector(object):
    def __init__(self):
        self.collection = []

    def collect(self, path):
        if not path.endswith('/'):
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


def push_middleware(get_response):
    def middleware(request):
        collector = FileCollector()
        storage.staticfiles_storage = staticfiles.staticfiles_storage = storage_factory(collector)()
        response = get_response(request)
        try:
            collection_copy = collector.collection.copy()
        except AttributeError:  # Python 2.7 compatibility
            collection_copy = list(collector.collection)
        urls = list(set(storage.staticfiles_storage.url(f) for f in collection_copy))
        response["Link"] = ", ".join(["<%s>; rel=preload" % url for url in urls[:10]])
        return response
    return middleware
