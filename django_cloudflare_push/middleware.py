"""Parse a page and add a Link header to the request, which CloudFlare can use to push static media to an HTTP/2 client."""
import django
from django.conf import settings
from django.contrib.staticfiles import storage
try:
    from django.contrib.staticfiles.templatetags import staticfiles
except ImportError:
    # django.contrib.staticfiles.templatetags.staticfiles removed in django 3.0
    # https://github.com/django/django/blob/a6b3938afc0204093b5356ade2be30b461a698c5/docs/releases/3.0.txt#L661
    from django.contrib.staticfiles import storage as staticfiles
from django.utils.functional import LazyObject



EXTENSION_AS = {
    'js': 'script',
    'css': 'style',
    'png': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'svg': 'image',
    'gif': 'image',
    'webp': 'image',
    'ttf': 'font',
    'woff': 'font',
    'woff2': 'font'
}
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
            # Try Solution to older Django versions using STATICFILES_STORAGE first
            try:
                configured_storage_cls = django.core.files.storage.get_storage_class(settings.STATICFILES_STORAGE)
            # Use the Django 5.1+ STORAGES setting if the first one fails
            except Exception: # 
                storage_backend = settings.STORAGES["staticfiles"]["BACKEND"]
                configured_storage_cls = django.utils.module_loading.import_string(storage_backend)
 
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


def create_header_content(urls):
    """
    Creates the content for the Link header.
    """
    links = []
    for url in urls[:10]:
        ext = url.rsplit(".")[-1].lower()
        if ext in EXTENSION_AS:
            link = "<%s>; rel=preload; as=%s" % (url, EXTENSION_AS[ext])
        else:
            link = "<%s>; rel=preload" % (url,)
        links.append(link)
    return ", ".join(links)


def push_middleware(get_response):
    def middleware(request):
        collector = FileCollector()
        storage.staticfiles_storage = staticfiles.staticfiles_storage = storage_factory(collector)()
        response = get_response(request)
        collection_copy = list(collector.collection)  # For compatibility with 2.7.
        urls = list(set(storage.staticfiles_storage.url(f) for f in collection_copy))
        urls = sort_urls(urls)
        response["Link"] = create_header_content(urls)
        return response
    return middleware
