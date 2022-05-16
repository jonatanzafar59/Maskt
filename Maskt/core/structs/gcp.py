from Maskt.core.pxLogManager import pxLogging
from Maskt.core.ConnectorManager import ConnectorManager


class pxGcpObject(pxLogging):
    def __init__(self):
        # DUMB CLASS - for later use
        super().__init__()


class pxGcpResponse(pxGcpObject):
    def __init__(self, payload):
        super().__init__()
        self._payload = payload

    def payload(self):
        return self._payload

    def field_to_list(self, field):
        return [x[field] for x in self._payload['items']]

    def filter(self, include_filter='', exclude_filter='None'):
        if 'items' in self._payload.keys():
            items = [x for x in self._payload['items']
                     if include_filter in x['name'] and exclude_filter not in x['name']]
            return items
        return []

    def search(self, field, value):
        for x in self._payload['items']:
            if x[field] == value:
                return x
        return None


class pxGcpRequest(pxGcpObject):
    def __init__(self, request):
        super().__init__()
        self.zone = request.uri.split('/')[8]
        self.project = request.uri.split('/')[6]
        self.connector = ConnectorManager(project=self.project).gcp
        self._current = request

    def exec(self):
        try:
            resp_pointer = self._current.execute()
            if self._current.method == 'GET':
                resp = resp_pointer
            else:
                resp = self._wait_for_operation(resp_pointer['name'])
            return pxGcpResponse(payload=resp)
        except Exception as e:
            self.connector.refresh()
            raise PxTaskGcpRequestError(e)

    def _wait_for_operation(self, operation):
        self.logger.info('Waiting for operation to finish...')
        while True:
            result = self.connector.service.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=operation).execute()
            if 'error' in result:
                raise RuntimeError(result['error'])
            return result


class PxTaskGcpRequestError(Exception):
    pass
