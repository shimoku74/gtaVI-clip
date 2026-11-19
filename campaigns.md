# Campaigns

Данные со страниц, видимых без входа, на 2026-11-19. **Перед вступлением проверь заново**:
бюджеты и ставки меняются ежедневно. `unknown` значит, что на публичной странице этого нет (правила за входом).

## Таблица

| name | platforms | rate per 1K views | min / max payout | budget | rules (public) | link |
|---|---|---|---|---|---|---|
| Dasgasd3m x RUCKUS GTA 6 | TikTok, YouTube Shorts | $2.00 | $10 / $150 | $1,000 | нужен **аккаунт именно про GTA 6**, лучше аккаунт клипов стримеров; читать бриф до публикации; остальное `unknown` | https://contentrewards.com/c/campaigns/051002dd-5c46-43d0-a446-43f2957ba3a9 |
| BenDaDonnn x Puffco GTA 6 | TikTok, IG, YouTube, X, Facebook | $1.00 | $10 / $400 | $10,000 | клипы BenDaDonnn **с продуктами PuffCo** во время GTA 6; остальное `unknown` | https://contentrewards.com/c/campaigns/bb66f9eb-b90e-4dd0-8cee-9f3cd566c9a0 |
| KreekCraft GTA 6 Clipping (ClipLaunch) | TikTok, IG, YouTube | $1.00 | $3 / $300 | $6,824 | в клипе оверлей KreekCraft и призыв смотреть его стрим; остальное `unknown` | https://contentrewards.com/c/campaigns/2eaa14fb-6927-4136-897e-b096e0d907d6 |
| GATTOUZ x GTA VI x 1WIN | TikTok, IG, X | $0.35 | $35 / $35.01 | $10,000 | 1 правило `unknown`; 1WIN это букмекер, смотри рекламные ограничения | https://contentrewards.com/c/campaigns/0123c725-0bb8-49fc-b60a-5affd894b66d |
| Kai Cenat $10K GTA 6 Pool | TikTok, Shorts, Reels, X | пул, делится по просмотрам; 66 участников | нет | $10,000 | `unknown` (за входом; ссылка «RULES HERE» на странице не отображается) | https://contentrewards.com/c/campaigns/1d2bcb00-c904-415f-aa82-f95b96baad86 |
| Lacy GTA VI Marathon Pool (Reach) | TikTok, Reels, Shorts, X | пул, делится по доле одобренных просмотров; 340 участников | нет | $12,500 | см. ниже | https://contentrewards.com/c/campaigns/a5c63fad-cd53-4b81-9305-4a2d1696872a |
| clip.tech Kai Cenat subathon | `unknown` | $2.00 | `unknown` | 62% из $25K | в Discord Clip Money; это не GTA | https://www.clip.tech/clippers |

## Lacy GTA VI Marathon Pool: правила (reachclipping.com/LACYGTA)
- **Чтобы попасть в раздел выплат, нужно набрать минимум 750 000 просмотров суммарно.** Для новичка это высокий порог.
- Источник: стрим, видео или клип Lacy из его GTA-марафона (с 18 ноября 2026); Lacy должен быть главным в кадре.
- Платформы: TikTok, Instagram Reels, YouTube Shorts, X.
- Аудитория: минимум 50% из англоязычных стран (США, Канада, Австралия, Великобритания, Новая Зеландия).
- В подписи или тексте на видео должно быть имя LACY, хештег `#LACY`.
- Логотипы запрещены; нельзя показывать Lacy в негативном свете; нельзя ИИ-контент, боты, хейт-фарм.
- Отправлять в Content Rewards (Whop) **в течение 30 минут после публикации**.
- Выплата после конца кампании, пул делится по доле одобренных просмотров. Один страйк, и тебя навсегда убирают из всех кампаний Reach.
- Длина клипа и срок выплаты на странице `unknown`.

## Что проверено в исходном коде страниц (2026-11-19)
- У Kai Cenat, KreekCraft, BenDaDonnn, Gattouz и Dasgasd3m публичного текста правил нет. Описание Kai Cenat заканчивается на «RULES HERE:» без ссылки, правила лежат в 3 закрытых файлах внутри Whop.
- Единственная публичная страница правил — reachclipping.com/LACYGTA (Lacy).
- В данных страницы Kai Cenat участников в пуле больше, чем показано на карточке: 66 на карточке и поле `poolSplit.creatorCount` = 404. Одобрено 108 клипов, выплачено $0. Конкуренция выше, чем кажется.
- Правила из-за входа нужно вставить вручную. Секции: Brief, Requirements, Rules и Reference files внутри кампании.

## Общее
- ContentRewards: комиссия 10%, выплата после конца кампании/пула, нужен Whop-аккаунт.
- clip.tech: выплата после конца кампании на PayPal, срок Net 30 и зависит от оплаты клиентом; 3 страновых тира.
- Не вступать в кампании, которые просят сливы, «play early», пиратство, фейковые аккаунты.
