# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 20:33:41 2019

@author: zys
"""

#https://www.jb51.net/article/49365.htm
# 找不到64位bit串，做不了“把64位的SimHash分成四个part，如果两个SimHash相似（海明距离小于等于3），根据鸽巢原理，必然有一个part是完全相同的”
# 并没有看懂simhash这里的做法
bits = 64
class simhash:

    #构造函数
    def __init__(self, tokens=[], hashbits=bits):       
        self.hashbits = hashbits
        self.hash = self.simhash(tokens);

    #toString函数   
    def __str__(self):
        return str(self.hash)

    #生成simhash值   
    def simhash(self, tokens):
        if tokens==[]:
            return 0
        v = [0] * self.hashbits
        for t in [self._string_hash(x) for x in tokens]: #t为token的普通hash值          
            for i in range(self.hashbits):
                bitmask = 1 << i
                if t & bitmask :
                    v[i] += 1 #查看当前bit位是否为1,是的话将该位+1
                else:
                    v[i] -= 1 #否则的话,该位-1
        fingerprint = 0
        for i in range(self.hashbits):
            if v[i] >= 0:
                fingerprint += 1 << i
        return fingerprint #整个文档的fingerprint为最终各个位>=0的和

    #求海明距离
    def hamming_distance(self, otherhash):
        x = (self.hash ^ otherhash) & ((1 << self.hashbits) - 1)
        tot = 0;
        while x :
            tot += 1
            x &= x - 1
        return tot

    #求相似度
    def similarity (self, otherhash):
        a = float(self.hash)
        b = float(otherhash)
        if a > b : return b / a
        else: return a / b

    #针对source生成hash值   (一个可变长度版本的Python的内置散列)
    def _string_hash(self, source):       
        if source == "":
            return 0
        else:
            x = ord(source[0]) << 7
            m = 1000003
            mask = 2 ** self.hashbits - 1
            for c in source:
                x = ((x * m) ^ ord(c)) & mask
            x ^= len(source)
            if x == -1:
                x = -2
            return x
        
    def simhashindex(self):
        return self.hash

#求海明距离
def hash_hamming_distance(thishash, otherhash,hashbits=bits):
    x = (thishash ^ otherhash) & ((1 << hashbits) - 1)
    tot = 0;
    while x :
        tot += 1
        x &= x - 1
    return tot

#求相似度
def hash_similarity (thishash, otherhash):
    a = float(thishash)
    b = float(otherhash)
    if a > b : return b / a
    else: return a / b
            
if __name__ == '__main__':
    from jieba import analyse
    s = '你是一个人工智能软件'
    hash1 = simhash(analyse.tfidf(s))
    hash1.simhashindex() #hash1的simhash值，64位bit转换成了

    s = '你是人工智障'
    hash2 = simhash(analyse.tfidf(s))
    hash2.simhashindex()
    s = '你是人工智能'
    hash3 = simhash(analyse.tfidf(s))
    hash3.simhashindex()
    print(hash1.hamming_distance(hash2.simhashindex()) , "   " , hash1.similarity(hash2.simhashindex()))
    print(hash1.hamming_distance(hash3.simhashindex()) , "   " , hash1.similarity(hash3.simhashindex()))