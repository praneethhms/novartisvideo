# Fills walk.tpl.html with the step timings from timeline.json -> walk.html
import json
open('walk.html', 'w').write(open('walk.tpl.html').read().replace('__STEPS__', json.dumps(json.load(open('timeline.json')))))
