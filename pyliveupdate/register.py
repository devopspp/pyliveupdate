#!/usr/bin/python
# coding=utf8
"""
# Author: lily
# Created Time : 2020-02-05 15:05:54

# File Name: register.py
# Description:

"""
def plu_register(reg_list):
    g_list = reg_list
    for item in g_list:
        if item == '__builtins__':
            continue
        print(item)
        if __builtins__.get(item) == None and item[:2] != '__' and item != 'plu_register':
            print('ADD TO BUILTIN:', item)
            __builtins__[item] = g_list[item]


