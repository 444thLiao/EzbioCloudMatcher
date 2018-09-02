# -*- coding: utf-8 -*-

class Sequence:
    def __init__(self, name):
        self.__name = name
        self.__seq = ''

    def __repr__(self):
        return self.__name + ': ' + self.__seq

    @property
    def name(self):
        return self.__name

    @property
    def seq(self):
        return self.__seq
    
    def LoadFrDoc(self, file):
        pass

    def LoadFrTxt(self, file):
        seq = None
        with open(file, "r") as f:
            seq = f.read()
        if not seq:
            return False
        self.__seq = seq
        return True

def UnitTest():
    seq = Sequence('')
    if not seq.LoadFrTxt(r"C:\Users\Zcy\Desktop\EzbioCloudSequenceMatch\MCCC 1A01601.txt"):
        print('fail to load seq')
        return False
    print(seq)
    return True

if __name__ == '__main__':
    UnitTest()