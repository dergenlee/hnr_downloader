import os
import gettext
import json
import traceback

i18nPath = os.path.abspath(os.path.dirname(__file__))
localePath = os.path.join(i18nPath, 'locale')
langFile = os.path.join(i18nPath, 'lang.json')

with open(langFile, 'r', encoding='utf-8') as f:
    try:
        l = json.load(f)
    except Exception:
        pass
    else:
        lng = l.get('language', 'zh_CN')

        try:
            lang = gettext.translation('hnr', localePath, languages=[lng])
        except Exception:
            traceback.print_exc()
            gettext.install('hnr', localePath)
        else:
            lang.install()
