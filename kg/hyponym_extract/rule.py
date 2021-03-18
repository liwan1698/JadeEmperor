"""
基于规则抽取上下位词
"""
import re
from pyhanlp import HanLP


class HyponomyExtraction:
    '''通过分词，看看是否符合情况'''
    def pos_filter(self, s):
        if not s:
            return []
        wds = [w.word for w in HanLP.segment(s)]
        pos = [str(w.nature) for w in HanLP.segment(s) if w.nature]

        if len(''.join(wds))<2:
            return []
        if 'n' not in pos and 'nhd' not in pos:
            return []
        return ''.join(wds)


    '''A是一种Ｂ'''
    def ruler1(self, string):
        data = []
        pattern = re.compile("(.*)是一(种|个|类)(.*)")
        res = pattern.findall(string)
        if res:
            sub = self.pos_filter(res[0][0])
            big = self.pos_filter(res[0][2])
            if sub and big:
                data.append([sub, big])
        return data

    '''A是B的一种'''
    def ruler2(self, string):
        data = []
        pattern = re.compile(r'(.*)是(.*)的一(种|个|类)')
        res = pattern.findall(string)
        if res:
            sub = self.pos_filter(res[0][0])
            big = self.pos_filter(res[0][1])
            if sub and big:
                data.append([sub, big])
        return data


    '''抽取主函数'''
    def extract(self, sent):
        data = []
        res1 = self.ruler1(sent)
        res2 = self.ruler2(sent)
        data += res1
        data += res2
        return data


if __name__ == "__main__":
    text1 = "无形的音乐是一种灵魂"
    text2 = "肺癌是癌症的一种"
    extract = HyponomyExtraction()
    ret = extract.extract(text1)
    print(ret)
