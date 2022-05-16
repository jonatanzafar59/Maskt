from Maskt.conf.runtime import *
from Maskt.core.task import PxTask, PxTaskFailure
from Maskt.core.structs.gcp import pxGcpRequest, pxGcpResponse
from Maskt.connectors.prom import PxPrometheusEmptyResult
from multiprocessing import Pool
import time

class ValidateComponentCpuThreshold(PxTask):
    timeout = 30
    retry_count = 2
    retry_delay = 30

    def __init__(
            self,
            billing_component,
            region=None,
            threshold=0.3,
            time_window='5m',
            mode="idle",
            custom_labels={},
            **kargs):
        self.threshold = float(threshold)
        self.time_windows = '5m'
        self.billing_component = billing_component
        self.mode = mode  # user/system/iowait/idle/etc taken from Prometheus node_cpu mode label
        core_labels = {
            'billing_component': billing_component,
            'mode': self.mode}
        self.labels = {**core_labels, **custom_labels}
        if region:
            self.labels['region'] = region
        super().__init__(**kargs)

    def run(self):
        self._validate_threshold(result=self._query())

    def _query(self):
        labels = connectorManager.prometheus.labels_to_string(self.labels)
        query = f"max(1 - avg(rate(node_cpu{{{labels}}}[{self.time_windows}])) by(instance))"
        return connectorManager.prometheus.custom_query(query=query)

    def _validate_threshold(self, result):
        if float(result) > self.threshold:
            raise PxTaskFailure(
                f'{self.billing_component} {self.mode} cpu rate is {result} is not within threshold {self.threshold}')
        self.logger.info(
            f"{self.billing_component} {self.mode} cpu rate is {result} - ok")


class ValidateMongoErrors(PxTask):
    timeout = 15
    retry_count = 3
    retry_delay = 60

    def __init__(self, billing_component, region, custom_labels={}, **kargs):
        core_labels = {
            'billing_component': billing_component,
            'region': region}
        self.labels = {**core_labels, **custom_labels}
        self.threshold = 5
        super().__init__(**kargs)

    def run(self):
        self._validate_mongodb_is_healthy(self._query_mongo_errors())

    def _query_mongo_errors(self):
        labels = connectorManager.prometheus.labels_to_string(
            labels=self.labels, regex=True)
        time_windows = '5m'
        query = f"count(sum(rate(pxcollector_mongo_error{{{labels}}}[{time_windows}])) by(instance, region,billing_component) > 0)"
        self.logger.debug(query)
        try:
            return connectorManager.prometheus.custom_query(query=query)
        except PxPrometheusEmptyResult:
            return 0

    def _validate_mongodb_is_healthy(self, errors_count):
        if int(errors_count) > self.threshold:
            raise PxTaskFailure(f'Mongo errors {errors_count} detected')
        self.logger.info(
            f"Mongo is healthy - {int(errors_count)} errors detected")


class ScaleRegionalComponentCapacity(PxTask):
    timeout = 60 * 60 * 2
    retry_count = 1
    retry_delay = 20

    def __init__(self, region, billing_component, mode, **kargs):
        self.region = region
        self.billing_component = billing_component
        self.mode = mode.lower()
        self.target_capacity = pxConf[region].component(
            billing_component)[f'hypesale_{self.mode}_scale_target']
        self.batch_size = pxConf[region].component(
            billing_component)[f'hypesale_{self.mode}_scale_batch_size']
        self._should_autoscaler_create = pxConf[region].component(
            billing_component)['hypesale_create_autoscale'] and self.mode == 'up'
        self._should_autoscaler_delete = pxConf[region].component(
            billing_component)['hypesale_delete_autoscale'] and self.mode == 'down'
        self._should_use_batch = False if self.batch_size == - \
            1 else True  # -1 = All at once
        super().__init__(**kargs)

    def pre_run(self):
        _is_primary_zone = not self._is_retrying()
        self._zone_level = 'primary' if _is_primary_zone else 'secondary'
        self.current_zone = pxConf[self.region].main_zone if _is_primary_zone else pxConf[self.region].secondary_zone

    def run(self):
        self.instance_groups = self.get_instance_groups()
        self.set_autoscalers()
        self.scale_zone_instance_groups()

    def set_autoscalers(self):
        for instance_group in self.instance_groups:
            if self._should_autoscaler_create or self._should_autoscaler_delete:
                SetGcpInstanceGroupAutoscaler(
                    instance_group=instance_group,
                    billing_component=self.billing_component,
                    zone=self.current_zone,
                    mode=self.mode)

        self.autoscalers = self.get_autoscalers()

    def get_autoscalers(self):
        request_pointer = connectorManager.gcp.service.autoscalers().list(
            project=gcp_project, zone=self.current_zone)
        return pxGcpRequest(request=request_pointer).exec()

    def get_instance_groups(self):
        request_pointer = connectorManager.gcp.service.instanceGroupManagers().list(
            project=gcp_project, zone=self.current_zone)
        response = pxGcpRequest(request=request_pointer).exec()
        include_filter = self._get_filter()
        return response.filter(include_filter=include_filter)

    def scale_zone_instance_groups(self):
        self.logger.info(
            f"Scaling '{self.billing_component}' in {self._zone_level} zone '{self.current_zone}'")
        workers = len(self.instance_groups)
        try:
            pool = Pool(processes=workers)
            pool.map(self._scale_instance_group_batch, self.instance_groups)
        except ValueError:
            self.logger.error(
                f"No '{self.billing_component}' instance group in {self._zone_level} zone '{self.current_zone}'")

    def _scale_instance_group_batch(self, instance_group):
        current_capacity = self.get_current_capacity(instance_group)
        self.logger.info(
            f"'{instance_group['name']}' current capacity is {current_capacity}")
        if self.mode == 'up':
            self._scale_up(instance_group, current_capacity)
        else:
            self._scale_down(instance_group, current_capacity)

    def _scale_up(self, instance_group, current_capacity):
        if current_capacity > self.target_capacity:
            raise PxTaskFailure(
                f"instance group '{instance_group['name']}' current capacity {current_capacity}"
                f"is higher than target capacity {self.target_capacity}, failing.")
        self.logger.info(
            f"Scaling up instance group '{instance_group['name']}' to {self.target_capacity} hosts")
        autoscaler = self.get_autoscaler(instance_group)
        should_scale = current_capacity < self.target_capacity
        while should_scale:
            batch_target_capacity = min(
                current_capacity + self.batch_size,
                self.target_capacity)
            SetGcpInstanceGroupCapacity(
                instance_group=instance_group,
                billing_component=self.billing_component,
                target_capacity=batch_target_capacity,
                zone=self.current_zone,
                mode=self.mode,
                autoscaler=autoscaler)
            current_capacity = batch_target_capacity
            should_scale = current_capacity < self.target_capacity
            self._sleep(should_scale)

    def _scale_down(self, instance_group, current_capacity):
        if current_capacity < self.target_capacity:
            raise PxTaskFailure(
                f"instance group '{instance_group['name']}' current capacity {current_capacity} "
                f"is lower than target capacity {self.target_capacity}, failing.")
        self.logger.info(
            f"Scaling down instance group '{instance_group['name']}' to {self.target_capacity} hosts")
        autoscaler = self.get_autoscaler(instance_group)
        should_scale = current_capacity > self.target_capacity
        while should_scale:
            batch_target_capacity = max(
                current_capacity - self.batch_size,
                self.target_capacity) if self._should_use_batch else self.target_capacity
            SetGcpInstanceGroupCapacity(
                instance_group=instance_group,
                billing_component=self.billing_component,
                target_capacity=batch_target_capacity,
                zone=self.current_zone,
                mode=self.mode,
                autoscaler=autoscaler)
            current_capacity = batch_target_capacity
            should_scale = current_capacity > self.target_capacity
            self._sleep(should_scale)

    def _get_filter(self):
        # Adding zone for excluding similar but different component, like
        # manual/single
        if is_prod:
            return f'{self.billing_component}-{self.current_zone}'
        return f'{self.billing_component}-lg-{self.current_zone}'

    def get_current_capacity(self, instance_group):
        autoscaler = self.get_autoscaler(instance_group)
        if autoscaler:
            return autoscaler['autoscalingPolicy']['minNumReplicas']
        else:
            return instance_group['targetSize']

    def get_autoscaler(self, instance_group):
        return self.autoscalers.search(
            field='target', value=instance_group['selfLink'])

    def _sleep(self, should_scale):
        mins = pxConf[self.region].component(
                    self.billing_component)['hypesale_batch_min_interval'] if is_prod else 0.1
        secs = 60 * mins  # wait for mongo
        if should_scale:
            self.logger.info(f"Sleeping for {str(mins)} minutes")
            if not dryRun:
                time.sleep(secs)

    # From prometheus - not used.
    # def _get_instance_group_current_capacity(self, instance_group):
    #     query = f'sum(count(node_memory_MemFree{{instance=~"{instance_group}-.*"}}) by(instance))'
    #     try:
    #         result = connectorManager.prometheus.custom_query(query=query)
    #     except PxPrometheusEmptyResult:
    #         result = 0
    #     return int(result)


class SetGcpInstanceGroupAutoscaler(PxTask):
    def __init__(self, instance_group, billing_component, zone, mode, **kargs):
        self.instance_group = instance_group
        self.billing_component = billing_component
        self.zone = zone
        self.region = zone[:-2]
        self.mode = mode.lower()
        self.autoscaler_name = f"{self.instance_group['name']}-autoscaler"
        super().__init__(**kargs)

    def pre_run(self):
        self.body = self._set_body()
 
    def run(self):
        if self.mode == 'up':
            self.logger.info(
                f"Creating '{self.instance_group['name']}' autoscaler")
            if not dryRun:
                self.create_autoscaler()
        else:
            self.logger.info(
                f"Deleting '{self.instance_group['name']}' autoscaler")
            if not dryRun:
                self.delete_autoscaler()

    def create_autoscaler(self):
        try:
            request_pointer = connectorManager.gcp.service.autoscalers().insert(
                project=gcp_project, zone=self.zone, body=self.body)
            pxGcpRequest(request=request_pointer).exec()
            time.sleep(1)
        except Exception as e:
            self.logger.info(
                f"'{self.instance_group['name']}' autoscaler already exists")

    def delete_autoscaler(self):
        try:
            request_pointer = connectorManager.gcp.service.autoscalers().delete(
                project=gcp_project, zone=self.zone, autoscaler=self.autoscaler_name)
            pxGcpRequest(request=request_pointer).exec()
            time.sleep(1)
        except Exception as e:
            self.logger.info(
                f"'{self.instance_group['name']}' autoscaler not found")

    def _set_body(self):
        return {
            "target": self.instance_group['selfLink'],
            "name": self.autoscaler_name,
            "autoscalingPolicy": pxConf[self.region].component(self.billing_component)['hypesale_autoscale_settings']
        }


class SetGcpInstanceGroupCapacity(PxTask):
    def __init__(
            self,
            instance_group,
            billing_component,
            target_capacity,
            zone,
            mode,
            autoscaler=False,
            **kargs):
        self.instance_group = instance_group
        self.billing_component = billing_component
        self.target_capacity = target_capacity
        self.zone = zone
        self.mode = mode
        self.autoscaler = autoscaler
        self.region = zone[:-2]
        super().__init__(**kargs)

    def pre_run(self):
        ValidateMongoErrors(
            billing_component="collector.*",
            region=self.region)
        ValidateComponentCpuThreshold(
            billing_component='mongodb', threshold=0.25)

    def run(self):
        self.scale()

    def post_run(self):
        query = f'sum(count(node_memory_MemFree{{instance=~"{self.instance_group["name"]}-.*"}}) by(instance))'
        self._validate_instance_group_capacity(query)

    def _validate_instance_group_capacity(self, query):
        if not (self.mode == 'down' and self.autoscaler):
            operator = ">=" if self.mode == 'up' else "<="
            connectorManager.prometheus.query_long_polling(
                query=query, operator=operator, desired_result=self.target_capacity)
        self.logger.info(
            f"'{self.instance_group['name']}' capacity change done")

    def set_ig_min_capacity(self):
        autoscalingPolicy = self._set_autoscale_policy()
        body = {
            'name': self.autoscaler['name'],
            'target': self.instance_group["selfLink"],
            'autoscalingPolicy': autoscalingPolicy}
        if not dryRun:
            request_pointer = connectorManager.gcp.service.autoscalers().update(
                project=gcp_project, zone=self.zone, body=body)
            response = pxGcpRequest(request=request_pointer).exec()

    def _set_autoscale_policy(self):
        maxNumReplicas = max(self.autoscaler['autoscalingPolicy']['maxNumReplicas'], self.target_capacity)
        self.logger.info(f"set minimum '{self.instance_group['name']}' to {self.target_capacity}")

        autoscalingPolicy = pxConf[self.region].component(self.billing_component)['hypesale_autoscale_settings']
        autoscalingPolicy['minNumReplicas'] = self.target_capacity
        autoscalingPolicy['maxNumReplicas'] = maxNumReplicas
        return  autoscalingPolicy

    def resize_ig_capacity(self):
        self.logger.info(
            f"'{self.instance_group['name']}' autoscale disabled, resizing to {self.target_capacity} instances")
        if not dryRun:
            request_pointer = connectorManager.gcp.service.instanceGroupManagers().resize(
                project=gcp_project,
                zone=self.zone,
                size=self.target_capacity,
                instanceGroupManager=self.instance_group['name'],
                requestId=None)
            response = pxGcpRequest(request=request_pointer).exec()

    def scale(self):
        if self.autoscaler:
            self.set_ig_min_capacity()
        else:
            self.resize_ig_capacity()
