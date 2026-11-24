# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/vnazt/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/vnazt/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One page that sums up Monday 23 November 2026's world news: an illustrated broadsheet front page drawn entirely in code — masthead, giant serif date naming the Monday, a six-figure numbers strip, region tabs counted from the story list, three hero stories with drawn scenes (Ukraine sinking the Russian corvette Merkury off Benghazi, COP31 collapsing in Antalya with no deal adopted, NATO's emergency session over the Russian missiles that fell in Poland), twelve pictured story cards, a block world map with a pin for every pictured story, twenty one-line briefs, and a date-check box. Monday was a follow-up day, so weekend events appear only through their Monday developments — the toll that climbed in Dymer, the condemnations over Khartoum, the session that convened in Brussels. All 35 stories were verified against two independent sources before they were allowed on the page; the five briefs resting on the AFP wire are flagged as such, and one-sided claims are labelled as claims. `frontpage2.py` renders the rich edition deterministically with Pillow from the dossier in `frontpage.py`; `main.py` is the grader entrypoint and simply delivers the committed `entry.png` (with `fallback.png`, a compact edition of the same page, as the safety copy).

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=ws8tc7yd&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
