# -*- coding: utf-8 -*-
import datetime
import json
import pathlib
import re
import unittest

from bazi.dayun_zhengyi import dayun_zhengyi, taisui_zhengyi
from bazi.engine import build_chart
from bazi.hehui import analyze
from bazi.huangli import get_huangli
from bazi.shensha import sanhe_star


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
        self.assertEqual(chart['真太阳时']['校正后'], '21:24')
        self.assertEqual(chart['四柱']['日']['干支'], '甲子')
        self.assertEqual(chart['四柱']['时']['干支'], '乙亥')

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
