from Maskt.connectors.prom import pxPrometheusConnector
from Maskt.connectors.gcp import pxGcpConnector
from .state import pxLogging


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(
                *args, **kwargs)
        return cls._instances[cls]

# Singelton
# If created once in a process, will return the already created object


class ConnectorManager(pxLogging, metaclass=Singleton):
    def __init__(self, project):
        super().__init__()
        self.project = project
        is_prod = True if self.project == 'prod-demo' else False
        self.prometheus = pxPrometheusConnector(
            thanos=True, is_prod=is_prod, auto_connect=True)
        self.gcp = pxGcpConnector()
