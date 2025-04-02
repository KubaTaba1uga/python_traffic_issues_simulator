import subprocess
import sys
import time

INTERFACE = "eth0"
DOWN_TIME = 0  # seconds interface is down
UP_TIME = 60  # seconds interface is up


def run(cmd):
    print(f"$ {cmd}")
    subprocess.run(
        cmd, shell=True, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr
    )


def renew_ip():
    run(f"dhclient -r {INTERFACE}")  # Release current IP lease
    run(f"ip addr flush dev {INTERFACE}")  # Ensure no old IP remains
    run(f"dhclient -v {INTERFACE}")  # Request new IP from DHCP


def enable_interface():
    run(f"ip link set {INTERFACE} up")
    renew_ip()


def main():
    print(f"🚨 Starting network flapping on {INTERFACE} (Ctrl+C to stop)")
    try:
        while True:
            print(f"🔻 Disabling {INTERFACE} for {DOWN_TIME}s")
            run(f"ip link set {INTERFACE} down")
            time.sleep(DOWN_TIME)

            print(f"🔼 Enabling {INTERFACE} for {UP_TIME}s and renewing DHCP")
            enable_interface()
            time.sleep(UP_TIME)
    except KeyboardInterrupt:
        print("\n🧹 Cleaning up, restoring interface...")
        enable_interface()
        print("✅ Interface restored.")


if __name__ == "__main__":
    main()
