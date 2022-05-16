from Maskt.conf.runtime import *
from Maskt.core.task import PxTask, PxTaskFailure
from Maskt.core.structs.gcp import pxGcpRequest, pxGcpResponse
from Maskt.connectors.prom import PxPrometheusEmptyResult
import time, json, hashlib


class ValidateAppIdRiskApiRate(PxTask):
    timeout = 60
    def __init__(
            self,
            app_id,
            threshold,
            time_window='5m',
            region=None,
            custom_labels={},
            **kargs):
        self.result = []
        self.threshold = float(threshold)
        self.time_windows = time_window
        self.app_id = app_id
        core_labels = {
            'app_id': self.app_id,
            'activity_type': 'risk_api'}
        self.labels = {**core_labels, **custom_labels}
        if region:
            self.labels['region'] = region
        super().__init__(**kargs)

    def run(self):
        result = self._query()
        self._validate_threshold(result=result)

    def _query(self):
        labels = connectorManager.prometheus.labels_to_string(self.labels)
        query = f"sum(rate(pxcollector_activity_received{{{labels}}}[{self.time_windows}])) by (region)"
        return connectorManager.prometheus.custom_query(query=query, extract_value=False)

    def _validate_threshold(self, result):
        result_list = []
        for item in result:
            _formatted_item = { 'name': item['metric']['region'], 'value': float(item['value'][1]) }
            if _formatted_item['value'] > self.threshold:
                result_list.append(_formatted_item)
        
        if result_list == []:
            raise PxTaskFailure(
                f'"{self.app_id}"" has no regions risk api rate within threshold {self.threshold}')
        self.result = result_list

class GetGcpZoneAutoscalers(PxTask):
    def __init__(self, zone, include_filter=None, **kargs):
        self.zone = zone
        self.include_filter = include_filter
        super().__init__(**kargs)


    def run(self):
        self.result = self._format(self._query())

    def _query(self):
        request_pointer = connectorManager.gcp.service.autoscalers().list(
                project=gcp_project, 
                zone=self.zone
            )
        response = pxGcpRequest(request=request_pointer).exec()
        return response.filter(include_filter=self.include_filter)

    def _format(self, items):
        autoscalers = {}
        for item in items:
            autoscalers[item['target']] = item['name']
        return autoscalers


class pxSetScaleScheduler(PxTask):
    timeout = 60 * 10
    retry_delay = 20

    def __init__(self, app_id, schedule, mode, billing_components, **kargs):
        self.app_id = app_id
        self.schedule = schedule
        self.mode = mode
        self.billing_components = billing_components
        super().__init__(**kargs)


    def pre_run(self):
        schedule_scale_reqsec_threshold = 5
        self.regions = ValidateAppIdRiskApiRate(app_id=self.app_id, threshold=schedule_scale_reqsec_threshold).result

    def run(self):
        for region in self.regions:
            zone = pxConf[region['name']].main_zone
            for billing_component in self.billing_components:
                instance_groups = GetBillingComponentGcpInstanceGroups(zone=zone, billing_component=billing_component).result
                include_filter = self._include_filter(billing_component, zone)
                autoscalers = GetGcpZoneAutoscalers(zone=zone, include_filter=include_filter).result

                minRequiredReplicas = pxConf[region['name']].component(billing_component)['schedule_scale_min_required_replicas']
                durationSec = pxConf[region['name']].component(billing_component)['schedule_scale_duration_sec']

                for instance_group in instance_groups:
                    autoscaler = autoscalers.get(instance_group['selfLink'], None)
                    if autoscaler:
                        SetGcpInstanceGroupAutoscalerScheduler(
                            minRequiredReplicas = minRequiredReplicas,
                            schedule = self.schedule,
                            durationSec = durationSec,
                            instance_group=instance_group,
                            autoscaler=autoscaler,
                            zone=zone,
                            mode=self.mode
                        )
            print("\n")

    def _include_filter(self, billing_component, zone):
        if is_prod:
            return f"{billing_component}-{zone}"
        return f"{billing_component.replace('-manual', '-lg')}-{zone}"

class SetGcpInstanceGroupAutoscalerScheduler(PxTask):
    def __init__(self, minRequiredReplicas, schedule, durationSec, instance_group, autoscaler, zone, timezone='UTC', mode=True, **kargs):
        self.minRequiredReplicas = minRequiredReplicas
        self.schedule = schedule
        self.durationSec = durationSec
        self.instance_group = instance_group
        self.autoscaler = autoscaler
        self.zone = zone
        self.region = zone[:-2]
        self.timezone = timezone
        self.mode = False if mode.lower() == 'down' else True
        super().__init__(**kargs)

    def pre_run(self):
        self.body = self._set_body()

    def post_run(self):
        self._validate()

    def run(self):
        self.action = 'Disabling ' if not self.mode else 'Creating '
        self.logger.info(
            f"{self.action} '{self.instance_group['name']}' scheduler")

        if not dryRun:
            self.set_scheduler()


    def set_scheduler(self):
        try:
            request_pointer = connectorManager.gcp.service.autoscalers().patch(
                project=gcp_project, zone=self.zone, autoscaler=self.autoscaler, body=self.body)
            pxGcpRequest(request=request_pointer).exec()
            time.sleep(2)
        except Exception as e:
            self.logger.error(e)

    def _validate(self):
        try:
            # self.logger.info(f"Validating '{self.instance_group['name']}' scheduler")
            request_pointer = connectorManager.gcp.service.autoscalers().get(
                project=gcp_project, zone=self.zone, autoscaler=self.autoscaler)
            response = pxGcpRequest(request=request_pointer).exec()
            is_created = response.payload()['autoscalingPolicy'].get('scalingSchedules', {}).get(self.scheduler_name, {})
            if is_created:
                self.logger.info(f"{self.scheduler_name} for '{self.instance_group['name']}' done")
            else:
                # self.logger.error(f"{response.payload()['autoscalingPolicy']}")
                self.logger.error(f"{self.scheduler_name} for '{self.instance_group['name']}' failed")

        except Exception as e:
            self.logger.error(e)

    def _set_body(self):
        self.scheduler_name = self.get_scheduler_name()
        schedule = {
            "minRequiredReplicas": self.minRequiredReplicas,
            "schedule": self.schedule,
            "timeZone": self.timezone,
            "durationSec": self.durationSec,
            "disabled": not self.mode,
            "description": "scheuler done via pxTask python"
        }
        body = {
            "name": self.autoscaler,
            "target": self.instance_group['selfLink'],
            "autoscalingPolicy": {
                "scalingSchedules": {
                    f'{self.scheduler_name}': schedule               
                }
            }
        }

        self.logger.debug(json.dumps(body))
        return body

    def get_scheduler_name(self):
        scheduler_string = f'{self.schedule}-{self.durationSec}'
        scheduler_string_to_bytes = bytes(scheduler_string, encoding='utf-8')
        hash_object = hashlib.md5(scheduler_string_to_bytes)
        return f'scheduler-{hash_object.hexdigest()}'

class GetBillingComponentGcpInstanceGroups(PxTask):
    def __init__(self, zone, billing_component, **kargs):
        self.billing_component = billing_component
        self.zone = zone
        self.region = zone[:-2]
        super().__init__(**kargs)

    def run(self):
        self.logger.info(f'Querying billing component "{self.billing_component}" instance groups for zone "{self.zone}"')
        self.result = self._query()

    def _query(self):
        request_pointer = connectorManager.gcp.service.instanceGroupManagers().list(
            project=gcp_project, zone=self.zone)
        response = pxGcpRequest(request=request_pointer).exec()
        return response.filter(include_filter=self._filter)

    def pre_run(self):
        # Adding zone for excluding similar but different component, like
        # manual/single
        self._filter = f'{self.billing_component}-{self.zone}'
