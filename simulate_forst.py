import signal
import subprocess
import sys
import time

INTERFACE = "eth0"
IFB = "ifb0"
START_RATE_KBIT = 1000 * 1000  # 1 Gbit
MIN_RATE_KBIT = 10
DECAY_INTERVAL = 10  # seconds
DECAY_PERCENT = 0.10  # -10% per step
INCREASE_PERCENT = 0.20  # +20% per step
HOLD_LOW_SECONDS = 120  # hold min for 2 minutes


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
    # Only add ifb0 if it doesn't already exist
    run(f"ip link show {IFB} || ip link add {IFB} type ifb")
    run(f"ip link set {IFB} up")


def clear_tc():
    run(f"tc qdisc del dev {INTERFACE} root")
    run(f"tc qdisc del dev {INTERFACE} ingress")
    run(f"tc qdisc del dev {IFB} root")


def shape_upload(rate_kbit):
    run(f"tc qdisc add dev {INTERFACE} root handle 1: htb default 10 r2q 1")
    run(
        f"tc class add dev {INTERFACE} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )


def shape_download(rate_kbit):
    run(f"tc qdisc add dev {INTERFACE} ingress")
    run(
        f"tc filter add dev {INTERFACE} parent ffff: protocol ip u32 match u32 0 0 "
        f"action mirred egress redirect dev {IFB}"
    )
    run(f"tc qdisc add dev {IFB} root handle 1: htb default 10")
    run(
        f"tc class add dev {IFB} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )


def change_rate(rate_kbit):
    print(f"⚙️ Updating rate to {rate_kbit} kbit")
    run(
        f"tc class change dev {INTERFACE} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )
    run(
        f"tc class change dev {IFB} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )


def handle_interrupt(signum, frame):
    print("\n🔧 Ctrl+C received, cleaning up...")
    clear_tc()
    print("✅ Network shaping removed.")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_interrupt)

    rate = START_RATE_KBIT
    setup_ifb()
    clear_tc()
    shape_upload(rate)
    shape_download(rate)

    print("🔽 Decaying bandwidth by 10% every 10s...")
    while rate > MIN_RATE_KBIT:
        time.sleep(DECAY_INTERVAL)
        rate = max(int(rate * (1 - DECAY_PERCENT)), MIN_RATE_KBIT)
        change_rate(rate)

    print(f"⏱ Holding at {rate} kbit for {HOLD_LOW_SECONDS} seconds...")
    time.sleep(HOLD_LOW_SECONDS)

    print("🔼 Increasing bandwidth by 20% every 10s...")
    while rate < START_RATE_KBIT:
        time.sleep(DECAY_INTERVAL)
        rate = min(int(rate * (1 + INCREASE_PERCENT)), START_RATE_KBIT)
        change_rate(rate)

    print("🏁 Full bandwidth restored. Script finished.")


if __name__ == "__main__":
    main()
