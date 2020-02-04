class PrefixNode(object):
    def __init__(self):
        self.data = []
        self.children = {} # arch:child
        pass
    
    def find_child(self, path):
        children = self.children
        if len(path) == 0:
            return self
        elif path[0] in children:
            return children[path[0]].find_child(path[1:])
        else:
            return None
    
    def add_child(self, path, nodedata):
        children = self.children
        if len(path) == 0:
            self.data.append(nodedata)
            return self
        elif path[0] in children:
            return children[path[0]].add_child(path[1:], nodedata)
        else:
            children[path[0]] = PrefixNode()
            return children[path[0]].add_child(path[1:], nodedata)
    
    def __tostr(self, arc, dent):
        nodestr = ''
        nodestr += dent
        nodestr += '{} -- data:{}'.format(arc, self.data)
        nodestr += '\n'
        dent += '  '
        for arc, c in self.children.items():
            nodestr += c.__tostr(arc, dent)
        return nodestr
    
    def __str__(self):
        return self.__tostr('', '')
    
    def __repr__(self):
        return self.__tostr('', '')
        
class PrefixTree(object):
    def __init__(self, sep='.'):
        self.root = PrefixNode()
        self.sep = sep
        
    def add(self, name, nodedata):
        path = name.split(self.sep)
        return self.root.add_child(path, nodedata)
    
    def get(self, name):
        path = name.split(self.sep)
        return self.root.find_child(path)
    
    def delete(self, name):
        ###TODO
        pass