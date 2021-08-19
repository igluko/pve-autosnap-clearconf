#!/usr/bin/python3

import re
import shutil
import datetime
import os
import subprocess

def print_separetor():
    input("(Press any key for continue...)")
    print
    print("---")
    print

def clean_cron():
    print("---")
    print("Current crontab is:")
    os.system('crontab -l')
    print("---")
    # save cron into file
    os.system('crontab -l > cron-old')
    # change cron and save into new file
    os.system('cat cron-old | grep -v /usr/local/bin/pve-autosnap | grep -v "# automatic snapshot for vmid" > cron-new')
    # install new cron file
    os.system('crontab cron-new')
    os.system('rm cron-old cron-new')
    # check results
    print("New crontab is:")
    os.system('crontab -l')

def backup_qemu():
    print("---")
    # Source path 
    src = '/etc/pve/local/qemu-server/'
    # Get timestump
    timestump = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # Destination path 
    dest = './backup_qemu-server/' + timestump
    # Copy the content of 
    # source to destination 
    destination = shutil.copytree(src, dest)
    print("backup qemu config files:", destination)

some_header = re.compile("\[.*\]")
autosnap_header = re.compile("\[autosnap_[0-9]{8}_[0-9]{6}\]")
autosnap_zfs = re.compile(".*@autosnap_[0-9]{8}_[0-9]{6}")
autosnap_section = False
autosnap_count = 0

def check_section(str):
    global autosnap_section, autosnap_count
    if autosnap_header.match(str):
        autosnap_section = True
        autosnap_count += 1
    elif some_header.match(str):
        autosnap_section = False


def clear_conf(path):
    global autosnap_section, autosnap_count
    autosnap_section = False
    autosnap_count = 0
    
    file = open(path, 'r')
    lines = file.readlines()
    file.close
    file = open(path, 'w')

    for line in lines:
        check_section(line)
        if autosnap_section:
            continue
        file.write(line)
    file.close
    print("Removed ", autosnap_count, "autosnap sections in file: ", path)

def get_configs(folder):
    file_list = os.listdir(folder)
    config_list = []
    pattern = re.compile('\d{3,4}.conf')
    for file in file_list:
        if pattern.match(file):
            config = os.path.join(folder, file)
            config_list.append(config)
    return config_list


def filter_zfs_snapshots(snap_list):
    zfs_destroy_list = []
    zfs_destroy_count = 0
    for snap in snap_list:
        if autosnap_zfs.match(snap):
            print(snap)
            zfs_destroy_list.append(snap)
            zfs_destroy_count += 1
    return zfs_destroy_list

if __name__ == '__main__':
    clean_cron()
    backup_qemu()
    print("---")
    config_list = get_configs('/etc/pve/local/qemu-server/')
    for config in config_list:
        clear_conf(config)
    print("---")
    cmd = 'zfs list -H -o name -t snapshot -r rpool/data'
    output = subprocess.run(cmd.split(), stdout=subprocess.PIPE, text=True)
    #print(output.stdout)
    zfs_list = output.stdout.splitlines()
    zfs_destroy_list = filter_zfs_snapshots(zfs_list)
    print("ZFS will destroy", len(zfs_destroy_list), "of", len(zfs_list), "snapshots")
    if len(zfs_destroy_list) == 0:
        exit()
    if input("are you sure? (y/n)") != "y":
        exit()
    for snap in zfs_destroy_list:
        os.system("zfs destroy " + snap)
