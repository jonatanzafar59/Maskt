import os
from Maskt.core.ConnectorManager import ConnectorManager
from Maskt.conf.conf import pxDevConf, pxProdConf

gcp_project = os.getenv('MASKT_GCP_PROJECT')
dryRun = (os.getenv('MASKT_DRYRUN', 'True').lower() == 'true')
is_prod = True if gcp_project == 'prod-demo' else False
connectorManager = ConnectorManager(project=gcp_project)
pxConf = pxProdConf if is_prod else pxDevConf