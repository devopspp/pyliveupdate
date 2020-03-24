import argparse
import subprocess,re
import ntpath
class CallNode:
    def __init__(self, func, hit = 0, callee = [], caller = None, time = 0):
        self.func = func
        self.hit = hit
        self.callee = set()
        self.caller = caller
        self.time_ = time

    def print(self):
        print(self.func, self.hit, self.callee, self.caller, self.time_)


    def rec_print(self, n=0):
        #if n>5:
        #    return
        print_stack = []
        print_stack.append([self, 0])
        while len(print_stack) != 0:
            fnode, count = print_stack.pop()
            print(count*"\t", fnode.func)
            for c in fnode.callee:
                print_stack.append([c, count+1])


class Callgraph:
    def __init__(self, roots = {}):
        self.roots = roots

    def print(self):
        for th in self.roots:
            self.roots[th].rec_print(0)
    


def process_func_logs(logfile='/tmp/pyliveupdate.log', 
                      output='pyliveupdate.folded',
                     output2='pyliveupdate.summary'):
    logs = open(logfile).readlines()
    thread_stack = {}
    thread_stack_node = {}
    thread_stack_str = {}
    
    for i, line in enumerate(logs):
        log = [l.strip() for l in line.split(';')]
        thread_ = '{}-{}'.format(log[2], log[3])
        func_name = '{}.{}'.format(log[7], log[8])
        #print('{}-{}'.format(func_name, log[9]))
        stack_node = thread_stack_node.get(thread_, {})
        if stack_node == {}:
            stack_node["#root"] = CallNode("#root")
            thread_stack_node[thread_] = stack_node
        stack_ = thread_stack.get(thread_, [])
        if stack_ == []:
            thread_stack[thread_] = []
            thread_stack[thread_].append(thread_stack_node[thread_]["#root"])
        stackstr = thread_stack_str.get(thread_, None) # if start ""
        if stackstr == None:
            thread_stack_str[thread_] = []
        if log[9] == 'func_begin':
            thread_stack_str[thread_].append(func_name)
            stackstr = ";".join(thread_stack_str[thread_])
            func_node = thread_stack_node[thread_].get(stackstr,  None)
            if func_node == None:
                func_node = CallNode(func_name)
                thread_stack_node[thread_][stackstr] = func_node
            func_node.caller = thread_stack[thread_][-1]
            thread_stack[thread_][-1].callee.add(func_node)
            thread_stack[thread_].append(func_node)
            #thread_stack[thread_][-2].print()
            #print("65: ", thread_stack_str)
        elif log[9] == 'func_end':
            while len(thread_stack[thread_]) > 1:
                if thread_stack[thread_][-1].func == func_name:
                    break
                thread_stack[thread_].pop()
                thread_stack_str[thread_].pop()
            if len(thread_stack[thread_]) == 1:
                print('Warning: Mismatch line {}: {}'.format(i, line))
                #return
            else:
                stackstr = ";".join(thread_stack_str[thread_])
                time_ = float(log[10])
                func_node = thread_stack_node[thread_].get(stackstr)            
                func_node.time_ += time_
                func_node.hit += 1
                thread_stack[thread_].pop()
                thread_stack_str[thread_].pop()
                #print("67: ", thread_stack_str)
                #stack_time[stackstr] = times_
                #thread_stack_time[thread_] = stack_time
        #thread_stack_node[thread_]["#root"].rec_print()
    for th in thread_stack:
        if len(thread_stack[th]) > 1:
            print('Warning: Mismatch pairs for process{}'.format(th))
            #return
    cg_dict = {}
    for th in thread_stack_node:
        root_node = thread_stack_node[th]["#root"]
        cg_dict[th] = root_node
    cg = Callgraph(cg_dict)
    #cg.print()

    f = open(output, 'w')
    f_sum = open(output2, 'w')
    for th in thread_stack_node:
        folded_stack = []
        stackstr = []
        f.write(th+' '+str(0)+'\n')
        f_sum.write(th+'\n')
        f_sum.write('function  hit  time/hit (ms)\n')
        stackstr.append(th)
        folded_stack.append([thread_stack_node[th]['#root'], False])
        while(len(folded_stack)):
            current, visit = folded_stack[-1]
            if not visit:
                #print('137:', current.func, visit)
                if current.func[0] != '#' and current.hit != 0:
                    tmp_str = (len(stackstr)-1)*'  '
                    tmp_str += '-' if len(stackstr) > 1 else ''
                    tmp_str +=  format('%s %d %.3f\n'%(current.func, current.hit, current.time_))
                    f_sum.write(tmp_str)
                    current.func += '`hit' + str(current.hit)
                    stackstr.append(current.func)
                folded_stack[-1][1] = True
                for c in current.callee:
                    #print('APPEND:', c)
                    folded_stack.append([c, False])
            else:
                #print('145:', current.func, visit)
                # pop it out
                current, visit = folded_stack.pop()
                if current.func[0] != '#' and current.hit != 0:
                    f.write(";".join(stackstr)+' '+ str(current.time_)+'\n')
                    stackstr.pop()
    f.close()
    f_sum.close()
    results = {}
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
