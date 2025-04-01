import signal
import subprocess
import sys
import time

INTERFACE = "eth0"
IFB = "ifb0"
START_RATE_KBIT = 1000000  # 1Gbit to simulate "no limit"
DECAY_INTERVAL = 10  # seconds
DECAY_PERCENT = 0.1
MIN_RATE_KBIT = 10  # Stop decaying below this


# Run a shell command and forward its I/O to the terminal
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


# Set up IFB virtual device
def setup_ifb():
    run("modprobe ifb")
    run(f"ip link add {IFB} type ifb")
    run(f"ip link set {IFB} up")


# Clear existing tc rules
def clear_tc():
    run(f"tc qdisc del dev {INTERFACE} root")
    run(f"tc qdisc del dev {INTERFACE} ingress")
    run(f"tc qdisc del dev {IFB} root")


# Initial upload shaping
def shape_upload(rate_kbit):
    run(f"tc qdisc add dev {INTERFACE} root handle 1: htb default 10")
    run(
        f"tc class add dev {INTERFACE} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )


# Initial download shaping
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


# Update rate dynamically
def change_rate(rate_kbit):
    print(f"⚙️ Updating rate to {rate_kbit} kbit")
    run(
        f"tc class change dev {INTERFACE} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )
    run(
        f"tc class change dev {IFB} parent 1: classid 1:10 htb rate {rate_kbit}kbit ceil {rate_kbit}kbit"
    )


# Ctrl+C handler
def handle_interrupt(signum, frame):
    print("\n🔧 Caught Ctrl+C, cleaning up...")
    clear_tc()
    print("✅ Network limits removed.")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_interrupt)

    rate = START_RATE_KBIT
    setup_ifb()
    clear_tc()
    shape_upload(rate)
    shape_download(rate)

    print("🚀 Bandwidth shaping started. Decaying 10% every 10s...")
    print("⏳ Press Ctrl+C to stop and reset.")

    while rate > MIN_RATE_KBIT:
        time.sleep(DECAY_INTERVAL)
        rate = int(rate * (1 - DECAY_PERCENT))
        change_rate(rate)

    print("📉 Minimum rate reached. Holding at", rate, "kbit")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
