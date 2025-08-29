import sys
from pprint import pprint
sys.path.append(r'D:/ERP_MIF_Maroc/FastApi_ERP_BackEnd_MIF_Maroc')
from app import main
app = main.app
for r in app.routes:
    methods = sorted(list(r.methods)) if hasattr(r, 'methods') and r.methods else []
    methods_str = ",".join(methods)
    print(f"{methods_str:10} {r.path}")
