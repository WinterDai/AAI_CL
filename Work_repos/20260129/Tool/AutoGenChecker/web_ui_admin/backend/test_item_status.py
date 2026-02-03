import sys
sys.path.insert(0, r'C:\Users\yuyin\Desktop\CHECKLIST_V4\Tool\AutoGenChecker')

from api.dashboard import get_item_status_from_excel

status = get_item_status_from_excel()
print(f'Total items: {len(status)}')
print('\nSample items:')
for i, (k, v) in enumerate(list(status.items())[:15]):
    print(f'  {k}: status={v["status"]}, owner={v["owner"]}')

# Check items from Chenwei Fan
print('\nChenwei Fan items:')
chenwei_items = {k: v for k, v in status.items() if v['owner'] == 'Chenwei Fan'}
print(f'Total: {len(chenwei_items)}')
for k, v in list(chenwei_items.items())[:10]:
    print(f'  {k}: {v["status"]}')
