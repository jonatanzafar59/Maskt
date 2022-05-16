from .structs.component import ComponentStruct
from .components import component_names


# class pxRegionComponentsConf(ComponentStruct):

class pxComponentConf(ComponentStruct):
    def __init__(self, name):
        super().__init__()
        self.name = name

        # defaults
        self._hypesale()
        self._schedule_scale()

    def _hypesale(self):
        self.hypesale_down_scale_batch_size = -1
        self.hypesale_down_scale_target = None
        self.hypesale_up_scale_batch_size = 2
        self.hypesale_up_scale_target = None
        self.hypesale_create_autoscale = False
        self.hypesale_delete_autoscale = False
        self.hypesale_autoscale_settings = {}
        self.hypesale_batch_min_interval = 10

    def _schedule_scale(self):
        self.schedule_scale_min_required_replicas = 10
        self.schedule_scale_duration_sec = 60 * 120

class pxComponentsConf(ComponentStruct):
    def __init__(self):
        super().__init__()
        self._setup_keys()

    def _setup_keys(self):
        for name in component_names:
            setattr(self, name, pxComponentConf(name=name))


class pxRegion():
    def __init__(self, name, main_zone, secondary_zone, zones=[]):
        self.name = name
        self.zones = zones
        self.main_zone = f'{name}-{main_zone}'
        self.secondary_zone = f'{name}-{secondary_zone}'
        self.components = pxComponentsConf()

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, input):
        if hasattr(self, '_components'):
            for key, value in input.items():
                if key in self._components.keys():
                    self._components[key].update(value)
                else:
                    raise NameError(f"Property {key} need to be templated")
        else:
            self._components = input

    def component(self, name):
        return self._components[name]
