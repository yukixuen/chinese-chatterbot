# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 18:15:14 2019

@author: zys
"""

#求海明距离
def hash_hamming_distance(thishash, otherhash,hashbits=64):
    x = (thishash ^ otherhash) & ((1 << hashbits) - 1)
    tot = 0;
    while x :
        tot += 1
        x &= x - 1
    return tot,'small' # smaller is more similar

#求相似度
def hash_similarity (thishash, otherhash):
    a = float(thishash)
    b = float(otherhash)
    if a > b : return b/a,'big' # bigger is more similar
    else: return a/b,'big'
            