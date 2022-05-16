from Maskt.conf.runtime import *
from Maskt.core.task import PxTask, PxTaskFailure, PxTaskValidationFailure, PxTaskExitGracefully
from Maskt.connectors.prom import PxPrometheusEmptyResult
from Maskt.core.structs.gcp import pxGcpRequest, pxGcpResponse
from Maskt.core.slack import pxSlack

class FindOutlinerInstance(PxTask):
    timeout = 60

    def __init__(
            self,
            billing_component,
            region,
            threshold,
            custom_labels={},
            **kargs):
        self.billing_component = billing_component
        self.region = region
        instance = self._get_instance_label()
        core_labels = {'instance': instance}
        self.labels = {**core_labels, **custom_labels}
        self.threshold = threshold
        super().__init__(**kargs)

    def run(self):
        try:
            self.output = self._query()
        except PxPrometheusEmptyResult:
            self.output = []

    def _query(self):
        labels = connectorManager.prometheus.labels_to_string(
            self.labels, regex=True)
        query = f"sum(kafka_consumer_consumer_fetch_manager_metrics_records_lag_max{{{labels}}}) by(instance, zone) > {self.threshold}"
        return connectorManager.prometheus.custom_query(
            query=query, extract_labels=True)

    def _get_instance_label(self):
        return f'{self.billing_component}-{self.region}.*'


class TerminateInstance(PxTask):
    timeout = 300

    def __init__(self, instance, zone, **kargs):
        self.instance = instance
        self.zone = zone
        super().__init__(**kargs)

    def run(self):
        self.logger.info(f"terminating '{self.instance}")
        if not dryRun:
            self._terminate()

    def post_run(self):
        self._validate_instance_termination()

    def _validate_instance_termination(self):
        query = f'time() - node_boot_time{{instance="{self.instance}"}}'
        if not dryRun:
            connectorManager.prometheus.query_long_polling(
                query=query, operator="<", desired_result=120)
        self.logger.info(f"'{self.instance} termination done")

    def _terminate(self):
        request_pointer = connectorManager.gcp.service.instances().delete(
            project=gcp_project, zone=self.zone, instance=self.instance)
        response = pxGcpRequest(request=request_pointer).exec()


class CleanRegionalUnfitKmmInstances(PxTask):
    def __init__(self, region, threshold, **kargs):
        self.region = region
        self.threshold = threshold
        super().__init__(**kargs)

    def pre_run(self):
        billing_component = 'kmm-bd-activities'
        self.input_list = FindOutlinerInstance(
            billing_component=billing_component,
            region=self.region,
            threshold=self.threshold).output

    def run(self):
        self._validate_cluster_is_healthy()
        self.victim_instance = self.input_list.pop()
        TerminateInstance(
            instance=self.victim_instance['instance'],
            zone=self.victim_instance['zone'])

    def post_run(self):
        pxslack = pxSlack()

        text = f"*Action:* Terminated instance :firecracker:\n*Name:* '{self.victim_instance['instance']}'\n"

        pxslack.post_message(
            channel='#unfit-alerts',
            text=text,
            task="CleanUnfitKMM",
            dry_run=dryRun)

    def _validate_cluster_is_healthy(self):
        if len(self.input_list) == 0:
            raise PxTaskExitGracefully(
                "All instances are fit, skipping termination")
        if len(self.input_list) > 2:
            raise PxTaskValidationFailure(
                f"More than 2 instances are considered unfit - cluster may be unhealthy - skipping termination")
