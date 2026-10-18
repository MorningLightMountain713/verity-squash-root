#!/usr/bin/python3
import argparse
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from verity_squash_root.config import read_config, LOG_FILE, CONFIG_FILE
from verity_squash_root.distributions.autodetect import autodetect_distribution
from verity_squash_root.efi import sign_tool
from verity_squash_root.file_names import configured_variants
from verity_squash_root.initramfs.dracut import Dracut
from verity_squash_root.main import create_image_and_sign_kernel, \
    sign_extra_files


def configure_logger(verbose: bool) -> None:
    loglevel = logging.INFO if not verbose else logging.DEBUG
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger()
    logger.handlers[0].setLevel(logging.DEBUG)
    logger.handlers[1].setLevel(loglevel)


def parse_params_and_run():
    os.umask(0o077)
    config = read_config()

    parser = argparse.ArgumentParser(
        description="Create signed efi binaries which mount a verified "
                    "squashfs (dm-verity) image\nas rootfs on boot "
                    "(in the initramfs/initrd), with a persistent or a\n"
                    "tmpfs (volatile) overlay on top.\n\n"
                    "Signing is done by the tool named in VSR_SIGN_TOOL, "
                    "called as\n`<tool> --output <out> <in>`. Scratch files "
                    "go in a fresh directory\nunder TMPDIR.\n\n"
                    "The configuration file is located at {}".format(
                        CONFIG_FILE),
                    formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbose",
                        action="store_true",
                        help="Show debug messages on the terminal")
    cmd_parser = parser.add_subparsers(dest="command", required=True)
    build_parser = cmd_parser.add_parser(
        "build",
        help="Build squashfs, verity-info, efi binaries and sign\nthem.")
    build_parser.add_argument(
        "--system-name",
        default="unknown",
        help="System name to embed in UKI credential (e.g., 'fluxos')")
    build_parser.add_argument(
        "--system-version",
        default="0",
        help="System version to embed in UKI credential (e.g., '2510')")
    cmd_parser.add_parser("sign-extra-files",
                          help="Sign all files specified in the EXTRA_SIGN "
                               "section in the config file.")
    args = parser.parse_args()
    configure_logger(args.verbose)

    logging.debug("Running: {}".format(sys.argv))
    logging.debug("Parsed arguments: {}".format(args))

    work_dir = None
    try:
        sign_tool()
        if args.command == "build":
            configured_variants(config)
            distribution = autodetect_distribution()
            work_dir = Path(tempfile.mkdtemp(prefix="verity_squash_root."))
            create_image_and_sign_kernel(
                config, distribution, Dracut(distribution), work_dir,
                system_name=args.system_name,
                system_version=args.system_version
            )
        elif args.command == "sign-extra-files":
            sign_extra_files(config)
    except BaseException as e:
        logging.error("Error: {}".format(e))
        logging.debug(e, exc_info=True)
        logging.error("For more info use the --verbose option "
                      "or look into the log file: {}".format(LOG_FILE))
        sys.exit(1)
    finally:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    parse_params_and_run()
