import inspect, sys, time
from bytecode import UNSET, Label, Instr, Bytecode, BasicBlock, ControlFlowGraph
import copy, types, os, pathlib

BINDNAMES = ['_parameters', '_returnvalues', '_righthands', '_lefthands', '_variable']

class FunctionAnalyzer(object):
    @staticmethod
    def extract_bytecode(func):
        return Bytecode.from_code(func.__code__)
    
    @staticmethod
    def extract_parameters(func):
        return list(inspect.signature(func).parameters.keys())
    
    @staticmethod
    def find_return(func_bytecode):
        endpoints = []
        for i, instr in enumerate(func_bytecode):
            if hasattr(instr, 'name') and instr.name == 'RETURN_VALUE':
                endpoints.append(i)
        return endpoints
    
    @staticmethod
    def find_all_lines(func_bytecode):
        lines = []
        last_linebegin = -1
        last_lineno = -1
        if len(func_bytecode) == 0:
            return lines
        
        for i, instr in enumerate(func_bytecode):
            if hasattr(instr, 'lineno') and instr.lineno != last_lineno:
                lines.append((last_lineno, last_linebegin, i))
                last_linebegin = i
                last_lineno = instr.lineno
        lines.append((last_lineno, last_linebegin, len(func_bytecode)))
                     
        return lines[1:]
    
    @staticmethod
    def filter_return(func_bytecode):
        return_lineno = []
        new_bytecode = []
        
        # -2 to filter the default return
        for instr in func_bytecode[:-2]:
            if hasattr(instr, 'name') and instr.name == 'RETURN_VALUE':
                return_lineno.append(instr.lineno)
            else:
                new_bytecode.append(instr)
        if len(return_lineno) > 0:
            print('Warning: do not use return in payload function, return line ignored.')

        return new_bytecode
    
    @staticmethod
    def set_bytecode_lineno(func_bytecode, lineno):
        for bc in func_bytecode:
            bc.lineno = lineno
        return func_bytecode
    
    @staticmethod
    def copy_bytecode(payload_bytecode, lineno):
        new_bytecode = []
        for bc in payload_bytecode:
            new_bytecode.append(Instr(bc.name, bc.arg, lineno=lineno))
        return new_bytecode

class FunctionInstrumenter(object):
    @staticmethod
    def _bind_parameters(payload_bytecode, bindname):
        payload_bytecode[0:0] = [Instr('LOAD_GLOBAL', arg='locals'),
                                 Instr('CALL_FUNCTION', arg=0),
                                 Instr('LOAD_ATTR', arg='copy'),
                                 Instr('CALL_FUNCTION', arg=0),
                                 Instr('STORE_FAST', arg=bindname)
                                ]
        return payload_bytecode
        
    @staticmethod
    def instrument_func_begin(func_bytecode, payload_func):
        payload_bytecode = FunctionAnalyzer.extract_bytecode(payload_func)
        payload_parameters = FunctionAnalyzer.extract_parameters(payload_func)
        #filter return line in payload
        payload_bytecode = FunctionAnalyzer.filter_return(payload_bytecode)
        
        #bind local variable 'parameters'
        if '_parameters' in payload_parameters:
            payload_bytecode = FunctionInstrumenter._bind_parameters(payload_bytecode, 
                                                                     '_parameters')
        #set payload lineno
        lineno = func_bytecode[0].lineno
        payload_bytecode = FunctionAnalyzer.set_bytecode_lineno(payload_bytecode, lineno)
        
        #inject payload
        func_bytecode[0:0] = payload_bytecode
        return func_bytecode
    
    @staticmethod
    def _bind_returnvalues(payload_bytecode, bindname):
        payload_bytecode[0:0] = [Instr('DUP_TOP'),
                                 Instr('STORE_FAST', arg=bindname)
                                ]
        return payload_bytecode     
    
    @staticmethod
    def instrument_func_end(func_bytecode, payload_func):
        payload_bytecode = FunctionAnalyzer.extract_bytecode(payload_func)
        payload_parameters = FunctionAnalyzer.extract_parameters(payload_func)
        #filter return line in payload
        payload_bytecode = FunctionAnalyzer.filter_return(payload_bytecode)
        
        #bind local variable 'returnvalues'
        if '_returnvalues' in payload_parameters:
            payload_bytecode = FunctionInstrumenter._bind_returnvalues(payload_bytecode,
                                                                       '_returnvalues')
        
        #inject payload before every return
        endpoints = FunctionAnalyzer.find_return(func_bytecode)
        for endpoint in reversed(endpoints):
            lineno = func_bytecode[endpoint].lineno
            new_payload_bytecode = FunctionAnalyzer.copy_bytecode(payload_bytecode, lineno)
            func_bytecode[endpoint:endpoint] = new_payload_bytecode
        return func_bytecode

class LineInstrumenter(object):
    @staticmethod
    def _bind_righthands(payload_bytecode, line_instructions, varnames, bindname, lineno):
        '''store right hand variables in a line to bindname as a dict
        '''
        new_bytecode = [Instr('BUILD_MAP', 0, lineno=lineno),
                       Instr('STORE_FAST', bindname, lineno=lineno),
                       ]
        
        all_uses = VariableInstrumenter.find_all_var_use(line_instructions)
        if len(varnames) == 0:
            varnames = [u[0] for u in all_uses]
        
        for vname, vuse in all_uses:
            if vname in varnames:
                vuse = FunctionAnalyzer.copy_bytecode(vuse, lineno)
                vuse.extend([Instr('LOAD_FAST', bindname, lineno=lineno),
                             Instr('LOAD_CONST', vname, lineno=lineno),
                             Instr('STORE_SUBSCR', lineno=lineno)
                            ])
                new_bytecode.extend(vuse)
               
        if len(new_bytecode) > 2:
            payload_bytecode[0:0] = new_bytecode
            return payload_bytecode
        else:
            return []
   
    @staticmethod
    def instrument_line_begin(func_bytecode, payload_func, lines):
        payload_bytecode = FunctionAnalyzer.extract_bytecode(payload_func)
        payload_parameters = FunctionAnalyzer.extract_parameters(payload_func)
        #filter return line in payload
        payload_bytecode = FunctionAnalyzer.filter_return(payload_bytecode)
        
        all_lines = FunctionAnalyzer.find_all_lines(func_bytecode)
        
        #instrument every line when lines==()
        if len(lines) == 0:
            lines = [l[0] for l in all_lines]
                     
        for lineno, begin, end in reversed(all_lines):
            if lineno in lines:
                line_instructions = func_bytecode[begin:end]
                new_payload_bytecode = FunctionAnalyzer.copy_bytecode(payload_bytecode, lineno)
                if '_righthands' in payload_parameters:
                    new_payload_bytecode = LineInstrumenter._bind_righthands(new_payload_bytecode, 
                                                           line_instructions, (), '_righthands', lineno)
                func_bytecode[begin:begin] = new_payload_bytecode
        return func_bytecode

    @staticmethod
    def _bind_lefthands(payload_bytecode, line_instructions, varnames, bindname, lineno):
        '''store left hand variables in a line to bindname as a dict
        '''
        new_bytecode = [Instr('BUILD_MAP', 0, lineno=lineno),
                        Instr('STORE_FAST', bindname, lineno=lineno)] 
        
        all_defs = VariableInstrumenter.find_all_var_def(line_instructions)
        if len(varnames) == 0:
            varnames = [d[0] for d in all_defs]
            
        for vname, vdef in all_defs:
            if vname in varnames:
                vdef = FunctionAnalyzer.copy_bytecode(vdef, lineno)    
                for instr in vdef:
                    instr.name = instr.name.replace('STORE', 'LOAD')
                vdef.extend([Instr('LOAD_FAST', bindname, lineno=lineno),
                             Instr('LOAD_CONST', vname, lineno=lineno),
                             Instr('STORE_SUBSCR', lineno=lineno),
                            ])
                new_bytecode.extend(vdef)
        
        if len(new_bytecode) > 2:
            payload_bytecode[0:0] = new_bytecode
            return payload_bytecode
        else:
            return []
    
    @staticmethod
    def instrument_line_end(func_bytecode, payload_func, lines):
        payload_bytecode = FunctionAnalyzer.extract_bytecode(payload_func)
        payload_parameters = FunctionAnalyzer.extract_parameters(payload_func)
        #filter return line in payload
        payload_bytecode = FunctionAnalyzer.filter_return(payload_bytecode)
        
        all_lines = FunctionAnalyzer.find_all_lines(func_bytecode)
        
        #instrument every line when lines==()
        if len(lines) == 0:
            lines = [l[0] for l in all_lines]
                     
        for lineno, begin, end in reversed(all_lines):
            if lineno in lines:
                line_instructions = func_bytecode[begin:end]
                new_payload_bytecode = FunctionAnalyzer.copy_bytecode(payload_bytecode, lineno)
                if '_lefthands' in payload_parameters:
                    new_payload_bytecode = LineInstrumenter._bind_lefthands(new_payload_bytecode, 
                                                    line_instructions, (), '_lefthands', lineno)
                func_bytecode[end:end] = new_payload_bytecode
            
        return func_bytecode
    
class VariableInstrumenter(object):
    @staticmethod
    def find_all_var_def(bytecode_):
        var_defs = []
        workstack = []
        for instr in bytecode_:
            if isinstance(instr, Instr):
                if instr.name == 'LOAD_ATTR':
                    workstack.append(instr)
                elif instr.name in ['LOAD_FAST','LOAD_GLOBAL','LOAD_NAME']:
                    workstack = [instr]
                elif instr.name in ['STORE_FAST','STORE_GLOBAL','STORE_NAME']:
                    varname = instr.arg
                    if varname not in BINDNAMES:
                        var_defs.append((varname, [instr]))
                    workstack = []
                elif instr.name in ['STORE_ATTR']:
                    workstack.append(instr)
                    varname= '.'.join([s.arg for s in workstack])
                    if varname not in BINDNAMES:
                        var_defs.append((varname, workstack))
                    workstack = []
                else:
                    workstack = []
        return var_defs
    
    @staticmethod
    def _bind_var_def(payload_bytecode, var_def, bindname, lineno):
        new_bytecode = FunctionAnalyzer.copy_bytecode(var_def, lineno)
        for instr in new_bytecode:
            instr.name = instr.name.replace('STORE', 'LOAD')
        new_bytecode.append(Instr('STORE_FAST', bindname, lineno=lineno))
        payload_bytecode[0:0] = new_bytecode
        return payload_bytecode
    
    @staticmethod
    def instrument_var_def(func_bytecode, payload_func, varnames):
        payload_bytecode = FunctionAnalyzer.extract_bytecode(payload_func)
        payload_parameters = FunctionAnalyzer.extract_parameters(payload_func)
        #filter return line in payload
        payload_bytecode = FunctionAnalyzer.filter_return(payload_bytecode)
        
        all_lines = FunctionAnalyzer.find_all_lines(func_bytecode)
                     
        for lineno, begin, end in reversed(all_lines):
            line_instructions = func_bytecode[begin:end]
            new_payload_bytecode = FunctionAnalyzer.copy_bytecode(payload_bytecode, lineno)
                    
            if '_variable' in payload_parameters:
                new_payload_bytecode = LineInstrumenter._bind_lefthands(new_payload_bytecode, 
                                                 line_instructions , varnames, '_variable', lineno)
            func_bytecode[end:end] = new_payload_bytecode
        return func_bytecode
        
    @staticmethod
    def find_all_var_use(bytecode_):
        var_uses = []
        workstack = []
        for instr in bytecode_:
            if isinstance(instr, Instr):
                if instr.name == 'LOAD_ATTR':
                    workstack.append(instr)
                else:
                    if len(workstack) != 0 and workstack[0].name != 'LOAD_ATTR':
                        varname= '.'.join([s.arg for s in workstack])
                        if not (hasattr(instr, 'arg') and instr.arg in BINDNAMES)\
                            and not varname in BINDNAMES:
                            var_uses.append((varname, workstack))
                    workstack = []
                    if instr.name in ['LOAD_FAST','LOAD_GLOBAL','LOAD_NAME']:
                        workstack = [instr]

        return var_uses
    
    @staticmethod
    def _bind_var_use(payload_bytecode, var_use, bindname, lineno):
        new_bytecode = FunctionAnalyzer.copy_bytecode(var_use, lineno)
        new_bytecode.append(Instr('STORE_FAST', bindname, lineno=lineno))
        payload_bytecode[0:0] = new_bytecode
        return payload_bytecode
    
    @staticmethod
    def instrument_var_use(func_bytecode, payload_func, varnames):
        payload_bytecode = FunctionAnalyzer.extract_bytecode(payload_func)
        payload_parameters = FunctionAnalyzer.extract_parameters(payload_func)
        #filter return line in payload
        payload_bytecode = FunctionAnalyzer.filter_return(payload_bytecode)
        
        all_lines = FunctionAnalyzer.find_all_lines(func_bytecode)
                     
        for lineno, begin, end in reversed(all_lines):
            line_instructions = func_bytecode[begin:end]
            new_payload_bytecode = FunctionAnalyzer.copy_bytecode(payload_bytecode, lineno)

            if '_variable' in payload_parameters:
                new_payload_bytecode = LineInstrumenter._bind_righthands(new_payload_bytecode, 
                                                    line_instructions, varnames, '_variable', lineno)
            func_bytecode[begin:begin] = new_payload_bytecode
        return func_bytecode

class Instrumenter(object):
    @staticmethod
    def instrument(target_code, jointpoint_payload):
        func_bytecode = Bytecode.from_code(target_code)
        beginpoint = 0
        endpoint = -2
        for jointpoint, payload_func in jointpoint_payload.items():
            if isinstance(jointpoint, str):
                jointpoint = (jointpoint,)
            if jointpoint[0] == 'func_begin':
                func_bytecode = FunctionInstrumenter.instrument_func_begin(func_bytecode, payload_func)
            elif jointpoint[0] == 'func_end':
                func_bytecode = FunctionInstrumenter.instrument_func_end(func_bytecode, payload_func)
            elif jointpoint[0] == 'line_before':
                lines = ()
                if type(jointpoint) == tuple and len(jointpoint) > 1:
                    lines = jointpoint[1]
                func_bytecode = LineInstrumenter.instrument_line_begin(func_bytecode, payload_func, lines)
            elif jointpoint[0] == 'line_after':
                lines = ()
                if type(jointpoint) == tuple and len(jointpoint) > 1:
                    lines = jointpoint[1]
                func_bytecode = LineInstrumenter.instrument_line_end(func_bytecode, payload_func, lines)
            elif jointpoint[0] == 'var_def':
                varnames = ()
                if type(jointpoint) == tuple and len(jointpoint) > 1:
                    varnames = jointpoint[1]
                func_bytecode = VariableInstrumenter.instrument_var_def(func_bytecode, payload_func, varnames)
            elif jointpoint[0] == 'var_use':
                varnames = ()
                if type(jointpoint) == tuple and len(jointpoint) > 1:
                    varnames = jointpoint[1]
                func_bytecode = VariableInstrumenter.instrument_var_use(func_bytecode, payload_func, varnames)
            else:
                #ToDo
                pass

        return func_bytecode.to_code()
