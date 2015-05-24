import logging
import os
import inspect

from opbeat.utils import wrapt


logger = logging.getLogger(__name__)


class AbstractInstrumentedModule(object):
    name = None

    instrument_list = [
        # List of (module, method) pairs to instrument. E.g.:
        # ("requests.sessions", "Session.send"),
    ]

    def __init__(self, client):
        """

        :param client: opbeat.base.Client
        """
        self.wrapped = None
        self.client = client

        assert self.name is not None

    def get_public_methods(self, cls):
        methods = inspect.getmembers(cls, predicate=inspect.ismethod)
        methods = [cls.__name__ + "." + f[0] for f in methods
                   if not f[0].startswith("_")]
        return zip([cls.__module__] * len(methods), methods)

    def get_instrument_list(self):
        return self.instrument_list

    def instrument(self):
        skip_env_var = 'SKIP_INSTRUMENT_' + str(self.name.upper())
        if skip_env_var in os.environ:
            logger.debug("Skipping instrumentation of %s. %s is set.",
                         self.name, skip_env_var)

        try:
            instrument_list = self.get_instrument_list()

            for module, method in instrument_list:
                    try:
                        wrapt.wrap_function_wrapper(module, method, self.call)
                    except ImportError:
                        # Could not import thing
                        logger.debug("Skipping instrumentation of %s. Module %s not found",
                                     self.name, module)
        except ImportError as ex:
            logger.debug("Skipping instrumentation of %s. %s",
                         self.name, ex)

    def call(self, wrapped, instance, args, kwargs):
        raise NotImplemented
