import argparse
import subprocess,re
import ntpath

def process_func_logs(logfile='/tmp/pyliveupdate.log', 
                      output='pyliveupdate.folded',
                     output2='pyliveupdate.summary'):
    logs = open(logfile).readlines()
    thread_stack = {}
    thread_stack_time = {}
    for i, line in enumerate(logs):
        log = [l.strip() for l in line.split(';')]
        thread_ = '{}-{}'.format(log[2], log[3])
        func_name = '{}.{}'.format(log[7], log[8])
        stack_ = thread_stack.get(thread_, [])
        if log[9] == 'func_begin':
            stack_.append(func_name)
        elif log[9] == 'func_end':
            stackstr = ';'.join(stack_)
            time_ = float(log[10])
            stack_time = thread_stack_time.get(thread_, {})
            times_ = stack_time.get(stackstr, [])
            times_.append(time_)
            stack_time[stackstr] = times_
            thread_stack_time[thread_] = stack_time
            if len(stack_) > 0:
                stack_.pop()
            else:
                print('mismatch line {}: {}'.format(i, line))
        thread_stack[thread_] = stack_
    results = {}
    
    with open(output2, 'w') as fout:
        for t, stack_time in thread_stack_time.items():
            result = []
            for s, st in stack_time.items():
                result.append((s,len(st),sum(st)/len(st)))
            result = sorted(result, key=lambda x: x[0])
            results[t] = result
            fout.write('{}\n'.format(t))
            fout.write('function  hit  time/hit (ms)\n')
            stack_ = []
            ident = 0
            for r in result:
                s = r[0]
                while len(stack_) > 0 and not s.startswith(stack_[-1]+';'):
                    stack_.pop()
                    ident -= 1
                if len(stack_)>0 and s.startswith(stack_[-1]):
                    olds = s
                    s = re.sub('^{};'.format(stack_[-1]), '', s)
                    stack_.append(olds)
                else:
                    ident = 0
                    stack_.append(s)

                if ident == 0:
                    fout.write('{} {}  {:.3f}\n'.format(s, r[1], r[2]))
                else:
                    fout.write('{}-{} {}  {:.3f}\n'.format('  '*ident, s, r[1], r[2]))
                ident += 1
            fout.write('\n')

    with open(output, 'w') as fout:
        for t, result in results.items():
            fout.write('{} {}\n'.format(t, 0))
            for i, r in enumerate(result):
                s = r[0]
                hit = r[1]
                time_=r[1]*r[2]
                lasts = s
                for j, r2 in enumerate(result[i:]):
                    if r2[0].startswith(s+';') or r2[0] == s:
                        if r2[0]!=s:
                            if lasts == s:
                                lasts = r2[0]
                                time_ -= r2[1]*r2[2]
                            elif not r2[0].startswith(lasts+';'):
                                lasts = r2[0]
                                time_ -= r2[1]*r2[2]
                        result[i+j] = (re.sub('^'+s, '{}`hit{}'.format(s, hit), r2[0]),
                                     r2[1], r2[2])
                    else:
                        break
                fout.write('{};{} {:.3f}\n'.format(t, result[i][0], time_))
    return results

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def main():
    parser = argparse.ArgumentParser(description='Process logs and generate a flame graph')
    parser.add_argument('-i', '--inputfile', type=str, default='/tmp/pyliveupdate.log',
                        help='the input log file (default: /tmp/pyliveupdate.log)')
#     parser.add_argument('-o', '--outputfile', type=str, default='pyliveupdate.svg',
#                         help='the output flamegraph file (default: pyliveupdate.svg)')
    args = parser.parse_args()
    inputname = path_leaf(args.inputfile)
    outputfolded = inputname + '.folded'
    outputsummary = inputname + '.summary'
    outputsvg = inputname + '.svg'
    process_func_logs(args.inputfile, outputfolded, outputsummary)
    subprocess.call("flamegraph.pl --countname 'ms' {} > {}".format(outputfolded, outputsvg), shell=True)
    print('generate summary: {} and flamegraph: {}'.format(outputsummary, outputsvg))
    
if __name__ == '__main__':
    main()