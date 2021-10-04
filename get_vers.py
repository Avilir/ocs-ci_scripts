#!/usr/bin/env python3

import os

'''
Image names:
➢ csi image version
e.g.
➢ oc describe pod csi-rbdplugin-provisioner-0 -n openshift-storage|grep Image
➢ oc describe pod csi-cephfsplugin-provisioner-0 -n openshift-storage|grep Image
➢ oc describe pod <any one csi plugin pod> -n openshift-storage|grep Image
'''
NS = "openshift-storage"

def run_oc_command(cmd):
    return os.popen(f"oc -n {NS} {cmd}").read()

def get_pod_name(filter):
    results = []
    for line in run_oc_command('get pod').split("\n"):
        if filter in line:
            results.append(str(line.split()[0].strip()))
    return results

def get_containers(pod):
    cmd = f'get pod {pod} -o jsonpath=' + "{.spec.containers[*].name}"
    results = run_oc_command(cmd).split("\n")
    return results

def header_write(log, text, tabs=0, nl=2):
    messagetext = ("\t" * tabs) + text + "\n"
    messageline = ("\t" * tabs) + ("=" * len(messagetext)) + ("\n" * nl)
    log.write(messagetext)
    log.write(messageline)

def command_output(log, cmd):
    for line in run_oc_command(cmd).split("\n"):
        log.write("\t\t" + line + "\n")

def driver_versions(log):
    header_write(log, "Driver versions")

    header_write(log, "OCP versions", tabs=1)
    command_output(log, 'version -o yaml')


    log.write("\t\tCluster version:\n\n")
    command_output(log, 'get clusterversion')

    header_write(log, "OCS versions", tabs=1)
    command_output(log, 'get csv')

    header_write(log, "Rook versions", tabs=1)
    pod = get_pod_name("tools")[0].replace("\u200b", '*')
    command = f'rsh {pod} rook version'
    command_output(log, command)

    header_write(log, "Ceph versions", tabs=1)
    command = f'rsh {pod} ceph version'
    command_output(log, command)

    header_write(log, "RHCOS versions", tabs=1)
    command = f'get node -o wide'
    command_output(log, command)

    header_write(log, "Ceph-CSI versions", tabs=1)
    pods = get_pod_name("csi-cephfsplugin")
    for pod in pods:
        log.write("\t\t" + pod + ":\n")
        conts = get_containers(pod)[0].split()
        for cont in conts:
            log.write("\t\t\t" + cont + ":\n")
            for line in run_oc_command(f'logs {pod} -c {cont} | head -n 2').split("\n"):
                if "version:" in line.lower():
                    log.write("\t\t\t  " + line.split(']')[1] + "\n")
    log.write("\n")

def img_name(log, pod_type):
    pods = get_pod_name(pod_type)
    for pod in pods:
        log.write("\t\t" + pod + ":\n")
        results = set()
        for line in run_oc_command(f'describe pod {pod}').split("\n"):
            if "image" in line.lower():
                results.add(line.strip())
        for line in sorted(results):
            log.write(f"\t\t  {line}\n")
        log.write("\n")
    log.write("\n")

def image_names(log):
    header_write(log, "Image versions")

    header_write(log, "Rook operator image version", tabs=1)
    img_name(log, "operator")

    header_write(log, "Ceph image version", tabs=1)
    img_name(log, "mon-a")

    header_write(log, "csi image version", tabs=1)
    img_name(log, "plugin")

def main():
    log = open("versions.log",'w')

    driver_versions(log)
    image_names(log)

    header_write(log, "run-ci versions collection")
    try:
        runci = os.popen("ls -1 ocs_version*").read().split('\n')[-2]
        with open(runci, 'r') as F:

            log.write(F.read())
        F.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
