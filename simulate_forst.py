import subprocess
import sys

INTERFACE = "eth0"
IFB = "ifb0"
RATE = "1mbit"


def run(cmd):
    print(f"$ {cmd}")
    subprocess.run(
        cmd,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )


def setup_ifb():
    run("modprobe ifb")
    run(f"ip link add {IFB} type ifb")
    run(f"ip link set {IFB} up")


def clear_tc():
    run(f"tc qdisc del dev {INTERFACE} root")
    run(f"tc qdisc del dev {INTERFACE} ingress")
    run(f"tc qdisc del dev {IFB} root")


def shape_upload():
    run(f"tc qdisc add dev {INTERFACE} root handle 1: htb default 10")
    run(
        f"tc class add dev {INTERFACE} parent 1: classid 1:10 htb rate {RATE} ceil {RATE}"
    )


def shape_download():
    run(f"tc qdisc add dev {INTERFACE} ingress")
    run(
        f"tc filter add dev {INTERFACE} parent ffff: protocol ip u32 match u32 0 0 "
        f"action mirred egress redirect dev {IFB}"
    )
    run(f"tc qdisc add dev {IFB} root handle 1: htb default 10")
    run(f"tc class add dev {IFB} parent 1: classid 1:10 htb rate {RATE} ceil {RATE}")


def main():
    setup_ifb()
    clear_tc()
    shape_upload()
    shape_download()
    print("✅ Bandwidth limited to", RATE, "on", INTERFACE)


if __name__ == "__main__":
    main()
