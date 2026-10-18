# verity-squash-root
## Build signed efi binaries which mount a dm-verity verified squashfs image as rootfs on boot.

A fork of [brandsimon/verity-squash-root](https://github.com/brandsimon/verity-squash-root)
for building FluxOS images on a build host. Signing is delegated to an external
tool (an HSM client); no secure-boot key is ever held locally.

The firmware verifies the signature of the UKI (unified kernel image); the UKI
verifies the squashfs root via dm-verity and mounts an overlay on top of it:

- **persistent**: the overlay's upper layer is the `overlay` directory on the
  root partition, so changes survive a reboot.
- **volatile**: the upper layer is a tmpfs, so every boot starts from the
  signed image and changes are held in RAM.

#### What happens on boot?

 - The initramfs mounts the root partition. Encryption of the root partition
   works as before; its cmdline parameters still need to be configured.
 - The image named by the cmdline's slot is verified via dm-verity and used.
   The build sets these parameters.
 - The overlay is set up as above, chosen by the cmdline parameter
   `verity_squash_root_volatile`.

## Usage

```
VSR_SIGN_TOOL=/path/to/signer verity-squash-root build \
    --system-name fluxos --system-version 1234
VSR_SIGN_TOOL=/path/to/signer verity-squash-root sign-extra-files
```

Environment:

- `VSR_SIGN_TOOL` (required): called as `<tool> --output <out> <in>` for every
  efi binary.
- `VSR_KERNEL_VERSIONS`: comma-separated kernel versions to build; unset builds
  every kernel in `/usr/lib/modules`.
- `TMPDIR`: scratch files (the squashfs image before it is moved into place,
  initramfs, unsigned UKI) go in a fresh directory under it, removed on exit.

A failure exits non-zero.

## Configuration

The config file is located at `/etc/verity_squash_root/config.ini`.

#### Section `DEFAULT`

- `CMDLINE` (required): the kernel cmdline.
- `EFI_STUB`: path to the efi stub, default is the one provided by systemd.
- `INCLUDE_DIRS`: directories the squashfs image is built from.
- `EXCLUDE_DIRS`: directories whose contents are left out of the image.
- `EFI_PARTITION`: efi binaries are written to
  `<EFI_PARTITION>/EFI/verity_squash_root/<os id>/`.
- `ROOT_MOUNT`: the image and its verity data are written to
  `<ROOT_MOUNT>/images/`, the root hash to `<ROOT_MOUNT>/root_hash`.
- `VARIANTS`: comma-separated, `persistent` and/or `volatile`. Each kernel gets
  `<name>.efi` for persistent and `<name>_tmpfs.efi` for volatile.

#### Section `EXTRA_SIGN`

Files signed by `sign-extra-files`, one per line:
```
NAME = SOURCE_PATH => DESTINATION_PATH
```

### Supported setups

Debian and Debian-like distributions with dracut.

## Files

On the root partition:

- `images/image_<slot>.squashfs`, `images/image_<slot>.squashfs.verity`
- `overlay`, `workdir`: the persistent overlay's directories

## Development

### Dependencies

```
binutils
cryptsetup-bin
dracut
python
squashfs-tools
systemd-boot-efi (only when no other efi-stub is configured)
```

Run unit tests:

```shell
python3 -m venv .venv
.venv/bin/pip install -e . --no-deps
.venv/bin/pip install pycodestyle pyflakes
.venv/bin/python -m unittest discover -s tests -t .
```
