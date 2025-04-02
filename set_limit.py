import subprocess
import sys

INTERFACE = "eth0"
IFB = "ifb0"
RATE_KBIT = 500  # Set to desired rate in kbit/s (e.g., 500 = 0.5Mbps)


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
    run(f"ip link show {IFB} || ip link add {IFB} type ifb")
    run(f"ip link set {IFB} up")


def clear_tc():
    run(f"tc qdisc del dev {INTERFACE} root")
    run(f"tc qdisc del dev {INTERFACE} ingress")
    run(f"tc qdisc del dev {IFB} root")


def apply_limit(rate_kbit):
    # Upload shaping
    run(f"tc qdisc add dev {INTERFACE} root handle 1: htb default 10")
    run(
        f"tc class add dev {INTERFACE} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )

    # Download shaping via IFB
    run(f"tc qdisc add dev {INTERFACE} ingress")
    run(
        f"tc filter add dev {INTERFACE} parent ffff: protocol ip u32 match u32 0 0 "
        f"action mirred egress redirect dev {IFB}"
    )
    run(f"tc qdisc add dev {IFB} root handle 1: htb default 10")
    run(
        f"tc class add dev {IFB} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )


def main():
    setup_ifb()
    clear_tc()
    apply_limit(RATE_KBIT)
    print(f"✅ Bandwidth limited to {RATE_KBIT / 1000:.2f} Mbps on {INTERFACE}")


if __name__ == "__main__":
    main()
