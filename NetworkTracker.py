import subprocess

def ping(host):
	cmd = ["ping", "-c", "1", host]
	return subprocess.call(cmd) == 0

if __name__ == "__main__":
	print("ping google dns")
	print("Status = ", ping("8.8.8.8"))
