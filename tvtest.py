import subprocess
import sys

cmd = "tvservice"
query = [cmd, '-s']
oncmd = [cmd, '-p']
offcmd = [cmd, '-o']

def runcmd(args):
	process = subprocess.Popen(args, stdout=subprocess.PIPE)
	output = process.stdout.readline()
	return output

def poweron():
	sudo = "sudo"
	chvt = "chvt"
	out = runcmd(oncmd)
	runcmd([sudo,chvt,"6"])
	runcmd([sudo,chvt,"7"])
	return out

def poweroff():
	return runcmd(offcmd)

output = runcmd(query)
print(output)
if (output.find('[TV is off]') != -1):
    print('OFF')
else:
    print('ON')

arg = None
print('args (' + str(len(sys.argv)) + ') ' + ' '.join(sys.argv))
if (len(sys.argv) > 1):
    arg = sys.argv[1]

cmd = None
if (arg == 'ON'):
    cmd=poweron
elif(arg == 'OFF'):
    cmd = poweroff
else:
    print("No args? " + ' '.join(sys.argv))

if (not cmd is None):
    out = cmd()
    print(out)
