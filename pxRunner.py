

import multiprocessing
if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')

import os
import argparse

def __main__():
    parser = get_default_parser()
    args, unknown = parser.parse_known_args()

    os.environ["MASKT_GCP_PROJECT"] = args.gcp_project
    os.environ["MASKT_DRYRUN"] = str(args.dry)
    os.environ["MASKT_LOGGING"] = "10" if args.debug else "20"

    runner = getattr(__import__(args.task), '__main__')
    runner(parser)

def get_default_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d", "--dry",
        action="store_true",
        default=False
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False
    )

    parser.add_argument(
        "--gcp-project",
        help="gcp project",
        default="dev-demo"
    )

    parser.add_argument(
        "--task",
        help="pxTask to execute"
    )
    
    return parser


if __name__ == '__main__':
    __main__()
