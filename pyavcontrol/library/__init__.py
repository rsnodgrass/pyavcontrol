from pyavcontrol.const import DEFAULT_MODEL_LIBRARIES
from pyavcontrol.library.model import DeviceModel

class DeviceModelLibrary:
    @staticmethod
    def create(library_dirs=DEFAULT_MODEL_LIBRARIES, event_loop=None):
        """
        Create an DeviceModelLibrary object representing all the complete
        library for resolving models and includes.

        If an event_loop argument is passed in this will return the
        asynchronous implementation. By default the synchronous interface
        is returned.

        :param library_dirs: paths used to resolve model names and includes (default=pyavcontrol's library)
        :param event_loop: to get an interface that can be used asynchronously, pass in an event loop

        :return an instance of DeviceLibraryModel
        """

        # NOTE: This is currently hardcoded to the YAML style libraries. May want to explore converting
        # this to Apple PKL instead, since that is more in line of the spirit of what model definitions are.
        if event_loop:
            from pyavcontrol.library.yaml_library import YAMLDeviceModelLibraryAsync
            return YAMLDeviceModelLibraryAsync(library_dirs, event_loop)

        from pyavcontrol.library.yaml_library import YAMLDeviceModelLibrarySync
        return YAMLDeviceModelLibrarySync(library_dirs)