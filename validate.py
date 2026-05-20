from template.template_20260424_2026 import SCHEMA_INSTRUMENT_RULES_EXTRACT2 as schema
print(len(schema))

from src.llm.mq_tag_summary import get_tag_summary
ds1 = get_tag_summary('2026_05_17_t1', model='deepseek-v4-flash', classification_prefix='class10')
mm1 = get_tag_summary('2026_05_17_t0', model='mimo-v2.5-pro', classification_prefix='class10')
ds2 = get_tag_summary('2026_05_17_t1', model='deepseek-v4-pro', classification_prefix='class10')
mm2 = get_tag_summary('2026_05_17_t1', model='mimo-v2.5-pro', classification_prefix='class10')
# outputs/reasoning/debug_2026_05_17_t1_*_deepseek-v4-flash/
# outputs/reasoning/debug_2026_05_17_t1_*_mimo-v2.5-pro/

print('deepseek (old , new):', len(ds1['raw2norm']), len(ds2['raw2norm']))
print('mimo (old , new):', len(mm1['raw2norm']), len(mm2['raw2norm']))

print('\nExist in deepseek, not in mimo')
# print('v1', [x for x in ds1['raw2norm'] if x not in mm1['raw2norm']  ])
print('v2', [x for x in ds2['raw2norm'] if x not in mm2['raw2norm']  ])

print('\nExist in mimo, not in deepseek')
# print('v1', [x for x in mm1['raw2norm'] if x not in ds1['raw2norm']  ])
print('v2', [x for x in mm2['raw2norm'] if x not in ds2['raw2norm']  ])

print('\nExist in v2, not in v1')
print('deepseek', [x for x in ds2['raw2norm'] if x not in ds1['raw2norm']  ])
print('mimo', [x for x in mm2['raw2norm'] if x not in mm1['raw2norm']  ])


print('\nExist in v1, not in v2')
print('deepseek', [x for x in ds1['raw2norm'] if x not in ds2['raw2norm']  ])


