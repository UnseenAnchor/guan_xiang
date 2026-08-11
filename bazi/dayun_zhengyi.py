# -*- coding: utf-8 -*-
"""大运/流年古籍参照 ← 《三命通会》卷二 (论大运/论小运/论太岁)
映射: 运干长生状态 → 吉凶原文; 太岁 vs 日干 → 岁运关系原文
"""
import json, os
from .ganzhi import shier_changsheng, shishen

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = None

def _load():
    global DATA
    if DATA is None:
        with open(os.path.join(_HERE, '..', 'knowledge', '大运流年_三命通会.json'), encoding='utf-8') as f:
            DATA = json.load(f)
    return DATA

# 长生状态 → 三命通会论大运吉凶
CHANGSHENG_RULE = {
    '长生': '行长生，主有创建作新之事。',
    '临官': '行临官，主兴盛快乐，发福进财，生子骨肉之庆。',
    '帝旺': '行帝旺，主兴盛快乐，发福进财，生子骨肉之庆。',
    '衰': '行至衰乡，多退败、破财、疾病等事。',
    '病': '行至病乡，多退败、破财、疾病等事。',
    '死': '行至死乡，主骨肉死丧，自身衰祸钝闷，百事蹇塞。',
    '绝': '行至绝乡，主骨肉死丧，自身衰祸钝闷，百事蹇塞。',
    '墓': '行至墓库成形之乡，百事得中，安康平易。',
    '胎': '行至胎库成形之乡，百事得中，安康平易。',
    '养': '行至胎库成形、冠带之乡，百事得中，安康平易。',
    '冠带': '行至冠带之乡，百事得中，安康平易。',
    '沐浴': '行至败运，主落魄懒惰，酒色昏迷。',
}

def dayun_zhengyi(rigan, dayun_gz):
    """大运断语 (三命通会): 运干十神 + 日主在运支的长生状态"""
    g, z = dayun_gz[0], dayun_gz[1]
    cs = shier_changsheng(rigan, z)
    rule = CHANGSHENG_RULE.get(cs, '')
    ss = shishen(rigan, g)
    return f'{dayun_gz}运: 运干{ss}，运支为日主十二长生之{cs}。{rule}'

def taisui_zhengyi(rigan, taisui_gz):
    """流年断语 (三命通会论太岁): 岁伤日干 / 日犯岁君"""
    g = taisui_gz[0]
    ss = shishen(rigan, g)
    # 岁伤日干: 岁干克日干; 日犯岁君: 日干克岁干
    from .ganzhi import gan_wuxing
    if gan_wuxing(g) == gan_wuxing(rigan):
        rel = '岁干与日干比和'
    elif _ke(gan_wuxing(g), gan_wuxing(rigan)):
        rel = '岁伤日干（岁干克日干）——譬君治臣，虽有灾晦，不为大害，何则？上治其下，顺也，其情尚未尽绝。'
    elif _ke(gan_wuxing(rigan), gan_wuxing(g)):
        rel = '日犯岁君（日干克岁干）——譬臣犯君，深为不利，下凌上，逆也，其凶决不能免。若五行有救，四柱有情，则灾可解。'
    elif _sheng(gan_wuxing(g), gan_wuxing(rigan)):
        rel = '岁干生日干'
    else:
        rel = '日干生岁干'
    return f'{taisui_gz}年: 岁干为日主之{ss}。{rel}'

def _ke(a, b):
    """五行 a 克 b?"""
    return {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}.get(a) == b

def _sheng(a, b):
    """五行 a 生 b?"""
    return {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}.get(a) == b

if __name__ == '__main__':
    for gz in ['壬午', '甲申', '乙酉', '丙戌', '丁亥']:
        print(dayun_zhengyi('庚', gz))
    for gz in ['庚午', '辛未', '甲戌']:
        print(taisui_zhengyi('庚', gz))
