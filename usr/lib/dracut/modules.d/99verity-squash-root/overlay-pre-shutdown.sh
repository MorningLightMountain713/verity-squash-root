#!/bin/sh

# The verity-squash-root root is an overlay whose upperdir and lowerdir are
# mounted *underneath* the root itself (set up by mount_handler at boot). After
# systemd-shutdown pivots into the initramfs the old root is /oldroot, and
# dracut's generic umount loop deadlocks on it: the overlay holds its upper/lower
# busy, and /oldroot cannot be unmounted while those submounts remain under it.
# The result is a "Cannot umount /oldroot" warning and the backing dm/loop
# devices are left for the kernel to tear down at reboot.
#
# Recursively lazy-detach the subtree before the umount loop runs, so /oldroot
# leaves the mount table and the freed dm-verity/loop devices can be removed by
# dm-shutdown. This is the shutdown-time counterpart to mount_handler.

if strstr "$(cat /proc/mounts)" " /oldroot "; then
    info "verity-squash-root: detaching overlay root before shutdown umount"
    umount -R -l /oldroot 2> /dev/null || umount -l /oldroot 2> /dev/null
fi
