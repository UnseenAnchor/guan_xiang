# -*- coding: utf-8 -*-
import datetime
import json
import pathlib
import re
import unittest

from bazi.dayun_zhengyi import dayun_zhengyi, taisui_zhengyi
from bazi.engine import build_chart
from bazi.ganzhi import nayin
from bazi.geju import judge_geju, strength_analysis
from bazi.hehui import analyze
from bazi.huangli import get_huangli
from bazi.shensha import sanhe_star
from bazi.solar_time import _equation_of_time


class EngineRegressionTests(unittest.TestCase):
    def test_flow_years_start_from_current_year(self):
        chart = build_chart(1990, 5, 15, 10, 30, sex=1)
        years = [item['年'] for item in chart['流年']]
        self.assertEqual(years, list(range(datetime.date.today().year, datetime.date.today().year + 5)))
        self.assertEqual(chart['流年'][0]['干支'], '丙午')

    def test_self_punishment_requires_two_equal_branches(self):
        result = analyze({'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'})
        self.assertNotIn(('地支自刑', '年', '午午', '午自刑'), result)
        self.assertNotIn(('地支自刑', '日', '辰辰', '辰自刑'), result)

        valid = analyze({'年': '甲辰', '月': '丙寅', '日': '戊辰', '时': '庚申'})
        self.assertEqual([item for item in valid if item[0] == '地支自刑'],
                         [('地支自刑', '年日', '辰辰', '辰自刑')])

    def test_half_combination_requires_two_distinct_members(self):
        result = analyze({'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'})
        self.assertFalse(any(item[0] == '地支半合' and item[2] == '巳巳' for item in result))

    def test_three_meeting_requires_all_three_distinct_members(self):
        result = analyze({'年': '庚午', '月': '辛巳', '日': '庚辰', '时': '辛巳'})
        self.assertFalse(any(item[0] == '地支三会' for item in result))

        valid = analyze({'年': '甲巳', '月': '丙午', '日': '戊未', '时': '庚申'})
        self.assertTrue(any(item[0] == '地支三会' and item[2] == '巳午未' for item in valid))

    def test_true_solar_time_rebuilds_pillars_and_date(self):
        chart = build_chart(2024, 1, 2, 0, 30, sex=1, longitude=75)
        self.assertEqual(chart['真太阳时']['校正日期'], '2024-01-01')
        self.assertEqual(chart['真太阳时']['校正后'], '21:27')
        self.assertEqual(chart['四柱']['日']['干支'], '甲子')
        self.assertEqual(chart['四柱']['时']['干支'], '乙亥')

    def test_equation_of_time_matches_noaa_seasonal_anchors(self):
        expected = {
            (2024, 1, 1): -2.90,
            (2024, 2, 11): -14.20,
            (2024, 4, 15): -0.05,
            (2024, 6, 14): 0.07,
            (2024, 11, 3): 16.36,
        }
        for date_parts, minutes in expected.items():
            with self.subTest(date=date_parts):
                self.assertAlmostEqual(_equation_of_time(*date_parts), minutes, delta=0.15)

    def test_month_branch_must_match_lu_or_ren_to_name_special_pattern(self):
        false_cases = [
            ({'年': '癸酉', '月': '壬戌', '日': '己卯', '时': '乙丑'}, '己'),
            ({'年': '辛丑', '月': '乙未', '日': '己巳', '时': '丙寅'}, '己'),
            ({'年': '庚辰', '月': '庚辰', '日': '戊午', '时': '甲寅'}, '戊'),
        ]
        for pillars, rigan in false_cases:
            with self.subTest(pillars=pillars):
                pattern = judge_geju(pillars, rigan, strength_analysis(pillars, rigan))
                self.assertNotIn(pattern[0], ('建禄格', '羊刃格'))

        for month, expected in [('寅', '建禄格'), ('卯', '羊刃格')]:
            pillars = {'年': '丙子', '月': '丙' + month, '日': '甲辰', '时': '庚午'}
            pattern = judge_geju(pillars, '甲', strength_analysis(pillars, '甲'))
            self.assertEqual(pattern[0], expected)

    def test_branch_without_day_master_element_is_not_counted_as_root(self):
        pillars = {'年': '癸酉', '月': '壬卯', '日': '己卯', '时': '乙酉'}
        strength = strength_analysis(pillars, '己')
        self.assertEqual(strength['得分项']['得地'], 0)
        self.assertIn('无根', strength['细节'][1])

    def test_start_luck_keeps_integer_and_exposes_full_precision(self):
        chart = build_chart(1993, 10, 25, 1, 25, sex=1)
        self.assertEqual(chart['起运'], 5)
        self.assertEqual(chart['起运详情'], {
            '年': 5, '月': 6, '日': 0, '时': 0,
            '交运时间': '1999-04-25 01:25',
            '算法': 'lunar-python sect=1',
        })

    def test_pillar_longsheng_fields_are_semantically_explicit(self):
        chart = build_chart(1990, 5, 15, 10, 30, sex=1)
        year = chart['四柱']['年']
        self.assertEqual(year['长生'], year['自坐长生'])
        self.assertEqual(year['日主地势'], '沐浴')
        self.assertEqual(year['自坐长生'], '沐浴')

    def test_nayin_uses_canonical_characters(self):
        self.assertEqual(nayin('庚辰'), '白蜡金')
        self.assertEqual(nayin('辛巳'), '白蜡金')
        self.assertEqual(nayin('壬子'), '桑柘木')
        self.assertEqual(nayin('癸丑'), '桑柘木')

    def test_no_longitude_keeps_civil_time(self):
        chart = build_chart(2024, 1, 2, 0, 30, sex=1)
        self.assertIsNone(chart['真太阳时'])
        self.assertEqual(chart['四柱']['日']['干支'], '乙丑')
        self.assertEqual(chart['四柱']['时']['干支'], '丙子')

    def test_late_zi_hour_uses_next_day_pillar(self):
        chart = build_chart(2024, 1, 1, 23, 30, sex=1)
        self.assertEqual(chart['四柱']['日']['干支'], '乙丑')
        self.assertEqual(chart['四柱']['时']['干支'], '丙子')

    def test_yima_mapping_covers_all_twelve_branches(self):
        expected = {
            '子': '寅', '丑': '亥', '寅': '申', '卯': '巳',
            '辰': '寅', '巳': '亥', '午': '申', '未': '巳',
            '申': '寅', '酉': '亥', '戌': '申', '亥': '巳',
        }
        self.assertEqual({zhi: sanhe_star(zhi, '驿马') for zhi in expected}, expected)

    def test_dayun_stage_uses_day_stem(self):
        reading = dayun_zhengyi('庚', '壬午')
        self.assertIn('沐浴', reading)
        self.assertIn('败运', reading)

    def test_taisui_generation_direction(self):
        self.assertIn('日干生岁干', taisui_zhengyi('庚', '壬午'))
        self.assertIn('岁干生日干', taisui_zhengyi('庚', '戊午'))

    def test_classical_readings_cover_all_effective_dayun(self):
        chart = build_chart(1990, 5, 15, 10, 30, sex=1)
        expected = len([item for item in chart['大运'][1:] if item.get('干支')])
        self.assertEqual(len(chart['运年断语']['三命通会']), expected)

    def test_huangli_returns_complete_xiu_name(self):
        info = get_huangli(2024, 2, 10)
        self.assertEqual(info['星宿全名'], info['星宿'] + info['七政'] + info['动物'])

    def test_yueling_corpus_is_complete_and_clean(self):
        path = pathlib.Path(__file__).parents[1] / 'knowledge' / '月令断语_穷通宝鉴_byAppTitle.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        expected = {f'{gan}日{zhi}月' for gan in '甲乙丙丁戊己庚辛壬癸'
                    for zhi in '寅卯辰巳午未申酉戌亥子丑'}
        self.assertEqual(set(data), expected)
        noise = re.compile(r'document\.|function|varprev|相关词条|热门词条|服务器暂时维护|'
                           r'书签添加|@中文百科全书|clientWidth|[\ue000-\uf8ff]', re.I)
        self.assertEqual([key for key, body in data.items() if noise.search(body)], [])
        self.assertEqual([key for key, body in data.items() if len(body.strip()) < 30], [])


if __name__ == '__main__':
    unittest.main()
