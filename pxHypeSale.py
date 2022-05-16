
# CLI example: python3 pxRunner.py
# --task pxHypeSale
# --gcp-project prod-demo
# --regions us-west1
# --billing-components microsvc-online microsvc-browser 
# --mode up
# --dry

import argparse
from Maskt.core.task import pxTaskManager
from Maskt.tasks.hype_sale import ScaleRegionalComponentCapacity

def __main__(defaultsParser):
    args = get_args(defaultsParser)
    regions = args.regions
    billing_components = args.billing_components
    mode = args.mode

    for region in regions:
        task = HypeSale(billing_components, region, mode)
        task.start()  # waiting for run to finish then to the next one

class HypeSale(pxTaskManager):
    def __init__(self, billing_components, region, mode):
        self.region = region
        self.billing_components = billing_components
        self.mode = mode
        super().__init__()

    def run(self):
        for billing_component in self.billing_components:
            task = ScaleRegionalComponentCapacity(
                region=self.region,
                billing_component=billing_component,
                mode=self.mode,
                auto_run=False)
            self.run_async(task)



def get_args(defaultsParser):
    parser = argparse.ArgumentParser(prog='pxHypeSale', add_help=False, parents=[defaultsParser])

    parser.add_argument(
        "-m", "--mode",
        required=True,
        choices=['up', 'down']
    )

    parser.add_argument(
        "--regions",
        nargs="+",
        required=True
    )

    parser.add_argument(
        "--billing-components",
        nargs="+",
        required=True
    )

    args = parser.parse_args()
    return args
