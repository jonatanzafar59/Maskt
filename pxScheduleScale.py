
# CLI example: python3 pxRunner.py
# --task pxScheduleScale
# --gcp-project prod-demo
# --schedule '0 0 30 1 * 2030'
# --mode up
# --dry

import argparse
from Maskt.core.task import pxTaskManager
from Maskt.tasks.schedule_scale import pxSetScaleScheduler

def __main__(defaultsParser):
    args = get_args(defaultsParser)
    app_id = args.app_id
    mode = args.mode
    schedule = args.schedule
    billing_components = args.billing_components

    task = pxScheduleScale(app_id, schedule, mode, billing_components)
    task.start()

class pxScheduleScale(pxTaskManager):
    def __init__(self, app_id, schedule, mode, billing_components):
        self.app_id = app_id
        self.schedule = schedule
        self.mode = mode
        self.billing_components = billing_components
        super().__init__()

    def run(self):
        task = pxSetScaleScheduler(
            app_id=self.app_id,
            schedule=self.schedule,
            mode=self.mode,
            billing_components=self.billing_components,
            auto_run=False)
        self.run_async(task)



def get_args(defaultsParser):
    parser = argparse.ArgumentParser(prog='pxScheduleScale', add_help=False, parents=[defaultsParser])

    parser.add_argument(
        "--app-id",
        required=True
    )

    parser.add_argument(
        "--schedule",
        required=True
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=['up', 'down']
    )

    parser.add_argument(
        "--billing-components",
        nargs="+",
        default=['microsvc-online-manual']
    )

    args = parser.parse_args()
    return args
