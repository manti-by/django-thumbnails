import os

from django.utils.encoding import smart_text, python_2_unicode_compatible

from . import conf
from . import backends
from . import post_processors
from . import processors


@python_2_unicode_compatible
class Thumbnail(object):
    """
    An object that contains relevant information about a thumbnailed image.
    """

    def __init__(self, metadata, storage, default=None):
        self.metadata = metadata
        self.storage = storage
        self.default = default
        self.name = getattr(metadata, 'name', None)

    def __str__(self):
        return smart_text(self.name or '')

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name or "None")

    def __eq__(self, other):
        try:
            return self.__dict__ == other.__dict__
        except AttributeError:
            return False

    def __bool__(self):
        return bool(self.name)

    def check_metadata(self):
        if self.metadata is None:
            raise ValueError('Thumbnail has no source file')

    @property
    def size(self):
        if self.default:
            return None
        self.check_metadata()
        return self.metadata.size

    def url(self):
        if self.default:
            return self.default
        self.check_metadata()
        return self.storage.url(self.name)


def get_thumbnail_name(source_name, size):
    name, extension = os.path.splitext(source_name)
    filename = "%s_%s%s" % (name, size, extension)
    return os.path.join(conf.BASEDIR, filename)


def create(source_name, size, metadata_backend=None, storage_backend=None):
    """
    Creates a thumbnail file and its relevant metadata. Returns a
    Thumbnail instance.
    """

    if storage_backend is None:
        storage_backend = backends.storage.get_backend()
    if metadata_backend is None:
        metadata_backend = backends.metadata.get_backend()

    thumbnail_file = processors.process(storage_backend.open(source_name), size)
    thumbnail_file = post_processors.process(thumbnail_file)
    name = get_thumbnail_name(source_name, size)
    name = storage_backend.save(name, thumbnail_file)

    metadata = metadata_backend.add_thumbnail(source_name, size, name)
    return Thumbnail(metadata=metadata, storage=storage_backend)


def get(source_name, size, metadata_backend=None, storage_backend=None):
    """
    Returns a Thumbnail instance, or None if thumbnail does not yet exist.
    """
    if storage_backend is None:
        storage_backend = backends.storage.get_backend()
    if metadata_backend is None:
        metadata_backend = backends.metadata.get_backend()

    metadata = metadata_backend.get_thumbnail(source_name, size)
    if metadata is None:
        return None
    else:
        return Thumbnail(metadata=metadata, storage=storage_backend)


def delete(source_name, size, metadata_backend=None, storage_backend=None):
    """
    Deletes a thumbnail file and its relevant metadata.
    """
    if storage_backend is None:
        storage_backend = backends.storage.get_backend()
    if metadata_backend is None:
        metadata_backend = backends.metadata.get_backend()
    storage_backend.delete(get_thumbnail_name(source_name, size))
    metadata_backend.delete_thumbnail(source_name, size)
