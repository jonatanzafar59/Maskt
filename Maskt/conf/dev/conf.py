from Maskt.core.pxRegion import pxRegion
from .overrides import *


# Region template, auto settings, enforcing protocol.
europe_west1 = pxRegion('europe-west1', main_zone='b', secondary_zone='c')
us_west1 = pxRegion('us-west1', main_zone='a', secondary_zone='b')

# overrides unique region settingsgit
# TODO: pxProdRegion && pxDevRegion on top of pxRegion.

# overrides only changed values!
europe_west1.components = europe_west1_overrides
us_west1.components = us_west1_overrides

# Example:
# from core.pxRegion import pxRegionConf
# europe_west1 = pxRegionConf('europe-west1') - Has default Config values - can print with 'europe_west1.conf'
# europe_west1.component('microsvc-online') - Gets specific component config
# europe_west1.component - print all components config


pxConf = {
    'europe-west1': europe_west1,
    'us-west1': us_west1,
}
