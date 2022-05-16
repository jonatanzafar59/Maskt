from Maskt.core.pxRegion import pxRegion
from .overrides import *

# Region template, auto settings, enforcing protocol.
europe_west1 = pxRegion('europe-west1', main_zone='b', secondary_zone='c')
europe_west3 = pxRegion('europe-west3', main_zone='a', secondary_zone='b')
asia_northeast1 = pxRegion('asia-northeast1', main_zone='a', secondary_zone='b')
asia_south1 = pxRegion('asia-south1', main_zone='b', secondary_zone='c')
us_west1 = pxRegion('us-west1', main_zone='a', secondary_zone='b')
us_east4 = pxRegion('us-east4', main_zone='b', secondary_zone='a')
us_east1 = pxRegion('us-east1', main_zone='b', secondary_zone='c')
us_central1 = pxRegion('us-central1', main_zone='a', secondary_zone='b')

# overrides unique region settingsgit
# TODO: pxProdRegion && pxDevRegion on top of pxRegion.

# overrides only changed values!
europe_west1.components = europe_west1_overrides
asia_south1.components = asia_south1_overrides
asia_northeast1.components = asia_northeast1_overrides
us_west1.components = us_west1_overrides


# Example:
# from core.pxRegion import pxRegionConf
# europe_west1 = pxRegionConf('europe-west1') - Has default Config values - can print with 'europe_west1.conf'
# europe_west1.component('microsvc-online') - Gets specific component config
# europe_west1.component - print all components config


pxConf = {
    'europe-west1': europe_west1,
    'europe-west3': europe_west3,
    'asia-northeast1': asia_northeast1,
    'asia-south1': asia_south1,
    'asia-northeast1': asia_northeast1,
    'us-west1': us_west1,
    'us-east4': us_east4,
    'us-east1': us_east1,
    'us-central1': us_central1
}
