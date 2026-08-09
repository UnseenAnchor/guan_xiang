# -*- coding: utf-8 -*-
"""
ganzhi.py — 干支基础层
提供干支、五行、十神、纳音、空亡与十二长生等基础数据。
"""
import json, os

_HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(_HERE, 'data_ny.json'), encoding='utf-8'))

GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']      # 十天干
ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']  # 十二地支
WUXING = ['木','火','土','金','水']                            # 五行 (相生序)
SHISHEN = ['比肩','劫财','食神','伤官','偏财','正财','七杀','正官','偏印','正印']  # 标准序
CHANGSHENG = ['长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养']

# ---------- 干支索引 ----------
def gan_index(g): return GAN.index(g)
def zhi_index(z): return ZHI.index(z)

def gan_wuxing(g):  return D['天干'][g]['wu_xing']
def gan_yinyang(g): return D['天干'][g]['yin_yang']
def zhi_wuxing(z):  return D['地支'][z]['wu_xing']
def zhi_yinyang(z): return D['地支'][z]['yin_yang']
def zhi_shengxiao(z): return D['地支'][z]['sheng_xiao']
def zhi_canggan(z): return D['地支'][z]['gan_str'].split(',')   # 藏干(本气->余气)
def zhi_canggan_wuxing(z): return D['地支'][z]['wuxing_str'].split(',')

# ---------- 六十甲子 ----------
JIAZI = [g+z for g, z in zip([GAN[i % 10] for i in range(60)], [ZHI[i % 12] for i in range(60)])]
def jiazi_index(gz):
    """干支 -> 六十甲子序号 (0-59)"""
    g, z = gz[0], gz[1]
    return ((gan_index(g) - zhi_index(z)) % 12) * 5 + gan_index(g) // 2 * 0 + 0 + (gan_index(g) // 2) * 6 + gan_index(g) % 2  # noqa
def jiazi_index_simple(gz):
    # 标准公式: 甲子=0, 索引 = (gan*6 - zhi*5) mod 60 的逆
    for i, x in enumerate(JIAZI):
        if x == gz: return i
    raise ValueError(gz)

def nayin(gz):
    """纳音: e.g. 甲子 -> 海中金"""
    return D['纳音'][gz]['wuxing']

def nayin_jian(gz):
    """纳音简五行"""
    return D['纳音'][gz]['wuxing_jian']

def xunkong(gz):
    """旬空亡: e.g. 甲子旬 -> 戌亥"""
    return D['纳音'][gz]['kong_wang'].split(',')

def gan_shengwang(gz):
    """干支坐支的长生状态 (如甲子->沐浴)"""
    return D['纳音'][gz]['gan_sheng_wang']

def gan_zhi_shengke(gz):
    """干支生克关系 (上生下/下生上/上下克/天地比)"""
    return D['纳音'][gz]['gan_zhi_sheng_ke']

# ---------- 十神 ----------
def shishen(rigan, other_gan):
    """日干 vs 其他天干 -> 十神"""
    return D['十神'][rigan + other_gan]

# ---------- 十二长生 (天干 对 地支) ----------
def shier_changsheng(g, z):
    """某天干 在 某地支 的长生状态"""
    return D['十二长生'][g + z]

# ---------- 五行生克 ----------
SHENG = {0: 1, 1: 2, 2: 3, 3: 4, 4: 0}  # 木->火->土->金->水->木
def wuxing_sheng(a, b):  # a 生 b?
    return SHENG[WUXING.index(a)] == WUXING.index(b)
def wuxing_ke(a, b):     # a 克 b?
    return SHENG[WUXING.index(b)] == WUXING.index(a)

# ---------- 合冲刑害 ----------
HE_GAN = {'甲':'己','乙':'庚','丙':'辛','丁':'壬','戊':'癸','己':'甲','庚':'乙','辛':'丙','壬':'丁','癸':'戊'}  # 天干五合
HE_ZHI = {'子':'丑','寅':'亥','卯':'戌','辰':'酉','巳':'申','午':'未','丑':'子','亥':'寅','戌':'卯','酉':'辰','申':'巳','未':'午'}  # 地支六合
CHONG_ZHI = {'子':'午','丑':'未','寅':'申','卯':'酉','辰':'戌','巳':'亥','午':'子','未':'丑','申':'寅','酉':'卯','戌':'辰','亥':'巳'}  # 六冲
XING_ZHI = {'子':'卯','卯':'子','寅':'巳','巳':'申','申':'寅','丑':'戌','戌':'未','未':'丑','辰':'辰','午':'午','酉':'酉','亥':'亥'}    # 三刑+自刑
HAI_ZHI = {'子':'未','丑':'午','寅':'巳','卯':'辰','申':'亥','酉':'戌'}  # 六害(子未丑午寅巳卯辰申亥酉戌)
SANHE_ZHI = {'申':'子辰','子':'辰申','辰':'申子','寅':'午戌','午':'戌寅','戌':'寅午','巳':'酉丑','酉':'丑巳','丑':'巳酉','亥':'卯未','卯':'未亥','未':'亥卯'}  # 三合局

def tian_gan_he(g): return HE_GAN.get(g)
def di_zhi_he(z):  return HE_ZHI.get(z)
def di_zhi_chong(z): return CHONG_ZHI.get(z)
def di_zhi_xing(z): return XING_ZHI.get(z)
def di_zhi_hai(z):  return HAI_ZHI.get(z)

if __name__ == '__main__':
    # 自测
    assert jiazi_index_simple('甲子') == 0
    assert jiazi_index_simple('癸亥') == 59
    print('甲子纳音:', nayin('甲子'), '| 空亡:', xunkong('甲子'))
    print('甲木在亥:', shier_changsheng('甲','亥'), '| 甲 vs 庚:', shishen('甲','庚'))
    print('六十甲子:', ' '.join(JIAZI[:10]), '...')
    print('子藏干:', zhi_canggan('子'), '| 辰藏干:', zhi_canggan('辰'))
    print('OK')
