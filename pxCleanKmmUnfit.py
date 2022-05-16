

# CLI example: python3 pxRunner.py
# --task pxCleanKmmUnfit
# --gcp-project prod-demo
# --regions us-east1
# --dry

import argparse
from Maskt.core.task import pxTaskManager
from Maskt.tasks.terminate_unfit_kmm import CleanRegionalUnfitKmmInstances

def __main__(defaultsParser):
    args = get_args(defaultsParser)
    regions = args.regions
    threshold = args.lag_threshold

    task = CleanUnfitKmmInstances(regions=regions, threshold=threshold)
    task.start()


def get_args(defaultsParser):
    parser = argparse.ArgumentParser(prog='pxUnfitInstance', add_help=False, parents=[defaultsParser])

    parser.add_argument(
        "--regions",
        nargs="+",
        required=True
    )

    parser.add_argument(
        "--lag-threshold",
        default='120000'
    )

    args = parser.parse_args()
    return args

class CleanUnfitKmmInstances(pxTaskManager):
    def __init__(self, regions, threshold):
        self.regions = regions
        self.threshold = threshold
        super().__init__()

    def run(self):
        for region in self.regions:
            task = CleanRegionalUnfitKmmInstances(
                region=region,
                threshold=self.threshold,
                auto_run=False)
            self.run_async(task)
