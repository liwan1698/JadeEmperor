"""
基于依存句法和语义角色标注的三元组抽取
"""
from pyhanlp import HanLP
import os, re


class TripleExtractor:
    def __init__(self):
        self.parser = HanlpParser()

    '''文章分句处理, 切分长句，冒号，分号，感叹号等做切分标识'''
    def split_sents(self, content):
        return [sentence for sentence in re.split(r'[？?！!。；;：:\n\r]', content) if sentence]


    '''三元组抽取主函数'''
    def ruler2(self, words, postags, child_dict_list, arcs):
        svos = []
        for index in range(len(postags)):
            # 使用依存句法进行抽取
            if postags[index]:
                # 抽取以谓词为中心的事实三元组
                child_dict = child_dict_list[index]
                # 主谓宾
                if '主谓关系' in child_dict and '动宾关系' in child_dict:
                    r = words[index]
                    e1 = self.complete_e(words, postags, child_dict_list, child_dict['主谓关系'][0])
                    e2 = self.complete_e(words, postags, child_dict_list, child_dict['动宾关系'][0])
                    svos.append([e1, r, e2])
                    print("谓语中心",[e1, r, e2])

                # 定语后置，动宾关系
                relation = arcs[index][0]
                head = arcs[index][2]
                if relation == '定中关系':
                    if '动宾关系' in child_dict:
                        e1 = self.complete_e(words, postags, child_dict_list, head - 1)
                        r = words[index]
                        e2 = self.complete_e(words, postags, child_dict_list, child_dict['动宾关系'][0])
                        temp_string = r + e2
                        if temp_string == e1[:len(temp_string)]:
                            e1 = e1[len(temp_string):]
                        if temp_string not in e1:
                            svos.append([e1, r, e2])
                            print("定语后置", [e1, r, e2])
                # 含有介宾关系的主谓动补关系
                if '主谓关系' in child_dict and '动补结构' in child_dict:
                    e1 = self.complete_e(words, postags, child_dict_list, child_dict['主谓关系'][0])
                    cmp_index = child_dict['动补结构'][0]
                    r = words[index] + words[cmp_index]
                    if '介宾关系' in child_dict_list[cmp_index]:
                        e2 = self.complete_e(words, postags, child_dict_list, child_dict_list[cmp_index]['介宾关系'][0])
                        svos.append([e1, r, e2])
                        print("介宾", [e1, r, e2])
        return svos

    '''对找出的主语或者宾语进行扩展'''
    def complete_e(self, words, postags, child_dict_list, word_index):
        child_dict = child_dict_list[word_index]
        prefix = ''
        if '定中关系' in child_dict:
            for i in range(len(child_dict['定中关系'])):
                prefix += self.complete_e(words, postags, child_dict_list, child_dict['定中关系'][i])
        postfix = ''
        if postags[word_index] == 'v' or postags[word_index] == 'vn':
            if '动宾关系' in child_dict:
                postfix += self.complete_e(words, postags, child_dict_list, child_dict['动宾关系'][0])
            if '主谓关系' in child_dict:
                prefix = self.complete_e(words, postags, child_dict_list, child_dict['主谓关系'][0]) + prefix

        return prefix + words[word_index] + postfix

    '''程序主控函数'''
    def triples_main(self, content):
        sentences = self.split_sents(content)
        svos = []
        for sentence in sentences:
            words, postags, child_dict_list, arcs = self.parser.parser_main(sentence)
            svo = self.ruler2(words, postags, child_dict_list, arcs)
            svos += svo
        return svos


class HanlpParser:
    def __init__(self):
        pass

    '''句法分析---为句子中的每个词语维护一个保存句法依存儿子节点的字典'''
    def build_parse_child_dict(self, arcs):
        words, postags = [], []
        child_dict_list = []
        format_parse_list = []
        for index in range(len(arcs)):
            words.append(arcs[index].LEMMA)
            postags.append(arcs[index].POSTAG)
            child_dict = dict()
            for arc_index in range(len(arcs)):
                if arcs[arc_index].HEAD.ID == index+1:   #arcs的索引从1开始
                    if arcs[arc_index].DEPREL in child_dict:
                        child_dict[arcs[arc_index].DEPREL].append(arc_index)
                    else:
                        child_dict[arcs[arc_index].DEPREL] = []
                        child_dict[arcs[arc_index].DEPREL].append(arc_index)
            child_dict_list.append(child_dict)
        rely_id = [arc.HEAD.ID for arc in arcs]  # 提取依存父节点id
        relation = [arc.DEPREL for arc in arcs]  # 提取依存关系
        heads = ['Root' if id == 0 else words[id - 1] for id in rely_id]  # 匹配依存父节点词语
        for i in range(len(words)):
            # ['定中关系', '李克强', 0, 'nh', '总理', 1, 'n']
            a = [relation[i], words[i], i, postags[i], heads[i], rely_id[i]-1, postags[rely_id[i]-1]]
            format_parse_list.append(a)

        return words, postags, child_dict_list, format_parse_list

    '''parser主函数'''
    def parser_main(self, sentence):
        arcs = HanLP.parseDependency(sentence).word
        words, postags, child_dict_list, format_parse_list = self.build_parse_child_dict(arcs)
        return words, postags, child_dict_list, format_parse_list


if __name__ == "__main__":
    sentence = "李克强总理今天来我家了,我感到非常荣幸"
    sentence2 = "以色列国防军20日对加沙地带实施轰炸，造成3名巴勒斯坦武装人员死亡。此外，巴勒斯坦人与以色列士兵当天在加沙地带与以交界地区发生冲突，一名巴勒斯坦人被打死。当天的冲突还造成210名巴勒斯坦人受伤。当天，数千名巴勒斯坦人在加沙地带边境地区继续“回归大游行”抗议活动。部分示威者燃烧轮胎，并向以军投掷石块、燃烧瓶等，驻守边境的以军士兵向示威人群发射催泪瓦斯并开枪射击。"

    # 分词和词性标注
    # terms = HanLP.segment(sentence)
    # for term in terms:
    #     print(term.word, term.nature)

    # 依存句法分析
    ret_dep = HanLP.parseDependency(sentence)
    print(ret_dep)

    extractor = TripleExtractor()
    svos = extractor.triples_main(sentence)
    print(svos)
