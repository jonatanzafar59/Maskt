from prometheus_api_client import PrometheusConnect
from Maskt.core.pxLogManager import pxLogging
import interruptingcow
import time
 
import operator

operators = {
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '=': operator.eq
}


class pxPrometheusHelper(pxLogging):

    def __init__(self):
        super().__init__()

    def labels_to_string(self, labels, regex=False):
        eq = '='
        if regex:
            eq = '=~'
        return ", ".join(f"{eq}".join((str(k), str(f'"{v}"')))
                         for k, v in labels.items())

    def extract_value(self, result):
        if result:
            return result[0]['value'][1]
        return '0'

    def extract_labels(self, result):
        return [x['metric'] for x in result]


class pxPrometheusConnector(pxPrometheusHelper):
    def __init__(
            self,
            region="us-central1",
            thanos=False,
            is_prod=False,
            auto_connect=True):
        super().__init__()
        self.region = region
        self.thanos = thanos
        self.is_prod = is_prod
        self.port = 10902 if self.thanos else 9090
        self.suffix = 'demo'
        self._url_prefix = 'thanos-query' if self.thanos else 'prometheus'
        self.url = self._set_url()
        if auto_connect:
            self.connection = self._connect()
        # print(self.url)

    def _set_url(self):
        return f'http://{self._url_prefix}-{self.region}.{self.suffix}:{self.port}'

    def _connect(self):
        connection = PrometheusConnect(url=self.url, disable_ssl=True)
        self.logger.info(f"Connected to prometheus '{self.url}'")
        return connection

    def custom_query(self, query, extract_labels=False, extract_value=True):
        self.logger.debug(query)
        result = self.connection.custom_query(query)
        if not result:
            # return 0 # DOTO: handle empty response
            raise PxPrometheusEmptyResult()
        if extract_labels:
            return self.extract_labels(result)
        if extract_value:
            result = self.extract_value(result)
        return result

    def query_long_polling(
            self,
            query,
            operator,
            desired_result,
            timeout=60 * 60,
            interval=15):
        self.logger.debug(f"Prometheus long polling starting")
        self.logger.debug(query)
        with interruptingcow.timeout(timeout, exception=PxPrometheusLongPollingTimeout):
            while True:
                result = self.connection.custom_query(query=query)
                value = self.extract_value(result)
                if self._compare(
                        float(value),
                        operator,
                        float(desired_result)):
                    self.logger.info(
                        f"result successfully {operator} desired result {desired_result}")
                    return True
                self.logger.info(
                    f"result {value} isn't {operator} {desired_result} - sleeping {interval} seconds")
                time.sleep(interval)

    def _compare(self, value, operator, desired_result):
        return operators[operator](value, desired_result)


class PxPrometheusEmptyResult(Exception):
    def __init__(self, message="'Prometheus query returned empty result'"):
        super().__init__(message)


class PxPrometheusLongPollingTimeout(Exception):
    def __init__(self, message="Prometheus long polling timed out"):
        super().__init__(message)
