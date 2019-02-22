import subprocess
import sys

cmd = "tvservice"
query = [cmd, '-s']
oncmd = [cmd, '-p']
offcmd = [cmd, '-o']
process = subprocess.Popen(query, stdout=subprocess.PIPE)

output = process.stdout.readline()
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
    cmd=oncmd
elif(arg == 'OFF'):
    cmd = offcmd
else:
    print("No args? " + ' '.join(sys.argv))

if (not cmd is None):
    cmdprocess = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    print('Executed ' + ' '.join(cmd))
    print(cmdprocess.stdout.readline())
