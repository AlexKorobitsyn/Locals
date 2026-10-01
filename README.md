Какая схема на деле:

https://habr.com/ru/articles/1005390/?ysclid=muggko1ykp177623640
Depends() - всё делается через него, изучить вопросик.
В идеале схема должна будет быть такая:

# есть root где находится главный интерфейс приложения 
# есть /me индивидуальная страница пользователя, определяется по токену 
# /me/playlists плейлисты сохранённые/добавленные(Там могут быть добавленные плейлисты другими пользователями типо сохранил альбом который добавил пользователь)
#  пользователем /me/playlists/{id_personal} Номер плейлиста в соответствии с dict {id_personal: id_real}
# /me/playlists/{id_personal}/{track_id_ps} Где тоже dictionary {track_id_ps: track_id_global} 
# /events по городу определяет локацию карты (город) и показывает события конкретные местные
# можно выбрать фильтр , концерты, jams, bands(ищу музыканта в группу)
# добавить лайки на песню и возможно быстрой оценки трека/альбома, рецензию через отдельную кнопку писать
# также есть разные левелы пользователей, которые определяются по кол-ву прослушиваний 
# и отзывов/рецензиций(или выддаётся админами уровень) Админы, модераторы, опытные, зелёные (админы / модеры могут добавлять события),
# Админы, модеры и Опытные могут выставлять жанры у трека и добавлять текст и их оценка более значимая для трека 
"""
/api/v1
│
├── /auth
│   ├── POST   /register
│   ├── POST   /login
│   ├── POST   /logout
│   ├── POST   /refresh
│   ├── POST   /password/reset
│   └── POST   /password/change
│
├── /me
│   │
│   ├── /profile                                  # расширенный профиль
│   │   ├── GET    /
│   │   ├── PATCH  /
│   │   ├── GET    /links
│   │   ├── PATCH  /links
│   │   ├── GET    /genres
│   │   ├── PATCH  /genres
│   │   └── /members                              # если type = band
│   │       ├── GET    /
│   │       ├── POST   /
│   │       ├── PATCH  /{userId}
│   │       └── DELETE /{userId}
│   │
│   ├── /tracks                                   # ← список треков для прослушивания (как в ВК)
│   │   ├── GET    /                              # ?sort=&limit=&offset=
│   │   ├── POST   /{trackId}                     # добавить трек в свой список
│   │   └── DELETE /{trackId}                     # убрать
│   │
│   ├── /likes                                    # всё лайкнутое (публично на профиле)
│   │   ├── /tracks
│   │   │   ├── GET    /
│   │   │   ├── POST   /{trackId}
│   │   │   └── DELETE /{trackId}
│   │   ├── /albums
│   │   │   ├── GET    /
│   │   │   ├── POST   /{albumId}
│   │   │   └── DELETE /{albumId}
│   │   ├── /artists
│   │   │   ├── GET    /
│   │   │   ├── POST   /{artistId}
│   │   │   └── DELETE /{artistId}
│   │   └── /playlists
│   │       ├── GET    /
│   │       ├── POST   /{playlistId}
│   │       └── DELETE /{playlistId}
│   │
│   ├── /playlists                                # свои + сохранённые чужие
│   │   ├── GET    /                              # ?role=owned|saved|all
│   │   ├── POST   /
│   │   └── /{playlistId}
│   │       ├── GET    /
│   │       ├── PATCH  /
│   │       ├── DELETE /
│   │       └── /tracks
│   │           ├── GET    /
│   │           ├── POST   /
│   │           ├── PATCH  /{trackId}             # порядок
│   │           └── DELETE /{trackId}
│   │
│   ├── /works                                    # созданное мной — «Мои творения»
│   │   ├── /tracks
│   │   │   ├── GET    /
│   │   │   ├── POST   /
│   │   │   └── /{trackId}
│   │   │       ├── GET    /
│   │   │       ├── PATCH  /
│   │   │       ├── DELETE /
│   │   │       └── /collaborators
│   │   │           ├── GET    /
│   │   │           ├── POST   /
│   │   │           └── DELETE /{userId}
│   │   └── /albums
│   │       ├── GET    /
│   │       ├── POST   /
│   │       └── /{albumId}
│   │           ├── GET    /
│   │           ├── PATCH  /
│   │           ├── DELETE /
│   │           └── /tracks
│   │               ├── GET    /
│   │               ├── POST   /
│   │               ├── PATCH  /{trackId}
│   │               └── DELETE /{trackId}
│   │
│   ├── /ratings
│   │   ├── /tracks
│   │   │   ├── GET    /
│   │   │   ├── PUT    /{trackId}
│   │   │   └── DELETE /{trackId}
│   │   └── /albums
│   │       ├── GET    /
│   │       ├── PUT    /{albumId}
│   │       └── DELETE /{albumId}
│   │
│   ├── /reviews
│   │   ├── GET    /
│   │   ├── POST   /
│   │   └── /{reviewId}
│   │       ├── GET    /
│   │       ├── PATCH  /
│   │       └── DELETE /
│   │
│   ├── /recommendations
│   │   ├── GET    /                              # ?type=track|album|artist|playlist|event
│   │   ├── GET    /tracks
│   │   ├── GET    /albums
│   │   ├── GET    /artists
│   │   ├── GET    /playlists
│   │   └── GET    /events
│   │
│   └── /feed
│       └── GET    /
│
├── /users
│   └── /{userId}
│       ├── GET    /                              # краткая карточка
│       ├── /profile
│       │   ├── GET    /
│       │   └── /members
│       │       └── GET    /
│       ├── /tracks                               # публичный список треков пользователя
│       │   └── GET    /
│       ├── /likes                                # публичные лайки — вкладки в профиле
│       │   ├── /tracks
│       │   │   └── GET    /
│       │   ├── /albums
│       │   │   └── GET    /
│       │   ├── /artists
│       │   │   └── GET    /
│       │   └── /playlists
│       │       └── GET    /
│       ├── /playlists                            # только публичные
│       │   └── GET    /
│       ├── /works
│       │   ├── GET    /tracks
│       │   └── GET    /albums
│       ├── /reviews
│       │   └── GET    /
│       └── /follow
│           ├── POST   /
│           └── DELETE /
│
├── /playlists
│   └── /{playlistId}                             # доступ: public или владелец
│       ├── GET    /
│       ├── /tracks
│       │   └── GET    /
│       └── /likes
│           ├── GET    /
│           ├── POST   /
│           └── DELETE /
│
├── /tracks
│   └── /{trackId}
│       ├── GET    /
│       ├── /reviews
│       │   ├── GET    /
│       │   └── POST   /
│       ├── /genres
│       │   ├── GET    /
│       │   ├── POST   /                          # privileged: сразу
│       │   ├── DELETE /{genreId}
│       │   └── /suggestions
│       │       ├── GET    /
│       │       └── POST   /
│       ├── /lyrics
│       │   ├── GET    /
│       │   ├── PUT    /                          # privileged: сразу
│       │   └── /suggestions
│       │       ├── GET    /
│       │       └── POST   /
│       ├── /similar
│       │   └── GET    /
│       ├── /like
│       │   ├── POST   /                          # = POST /me/likes/tracks/{id}
│       │   └── DELETE /
│       ├── /rating
│       │   ├── PUT    /
│       │   └── DELETE /
│       └── /stream
│           └── GET    /
│
├── /albums
│   └── /{albumId}
│       ├── GET    /
│       ├── /tracks
│       │   └── GET    /
│       ├── /reviews
│       │   ├── GET    /
│       │   └── POST   /
│       ├── /like
│       │   ├── POST   /
│       │   └── DELETE /
│       └── /rating
│           ├── PUT    /
│           └── DELETE /
│
├── /artists
│   └── /{artistId}
│       ├── GET    /
│       ├── /albums
│       │   └── GET    /
│       ├── /tracks
│       │   └── GET    /
│       ├── /like
│       │   ├── POST   /
│       │   └── DELETE /
│       └── /follow
│           ├── POST   /
│           └── DELETE /
│
├── /genres
│   ├── GET    /
│   └── /{genreId}
│       └── GET    /
│
├── /search
│   └── GET    /                                  # ?q=&type=track|album|artist|playlist|event
│
├── /events
│   ├── GET    /                                  # ?city=&type=&genre=&date=
│   │                                             # &lat=&lng=&radius=&limit=&offset=
│   ├── POST   /                                  # privileged
│   ├── /clusters
│   │   └── GET    /                              # ?lat=&lng=&zoom=
│   ├── /categories
│   │   └── GET    /
│   └── /{eventId}
│       ├── GET    /
│       ├── PATCH  /                              # privileged
│       ├── DELETE /                              # privileged
│       ├── /participants
│       │   ├── GET    /
│       │   ├── POST   /
│       │   └── DELETE /{userId}
│       ├── /join
│       │   ├── POST   /
│       │   └── DELETE /
│       └── /like
│           ├── POST   /
│           └── DELETE /
│
└── /admin
    │
    ├── /users
    │   └── /{userId}
    │       ├── GET    /
    │       ├── PATCH  /level
    │       ├── POST   /ban
    │       ├── DELETE /ban
    │       ├── POST   /verify
    │       └── DELETE /verify
    │
    ├── /events
    │   ├── GET    /
    │   ├── POST   /
    │   └── /{eventId}
    │       ├── PATCH  /
    │       └── DELETE /
    │
    ├── /tracks
    │   └── /{trackId}
    │       ├── PATCH  /
    │       ├── /genres
    │       │   ├── POST   /
    │       │   └── DELETE /{genreId}
    │       └── /lyrics
    │           └── PUT    /
    │
    ├── /moderation
    │   ├── /genres
    │   │   ├── GET    /
    │   │   ├── POST   /{suggestionId}/approve
    │   │   └── POST   /{suggestionId}/reject
    │   ├── /lyrics
    │   │   ├── GET    /
    │   │   ├── POST   /{suggestionId}/approve
    │   │   └── POST   /{suggestionId}/reject
    │   └── /reviews
    │       ├── GET    /
    │       ├── POST   /{reviewId}/approve
    │       └── POST   /{reviewId}/reject
    │
    ├── /genres
    │   ├── POST   /
    │   ├── PATCH  /{genreId}
    │   └── DELETE /{genreId}
    │
    └── /stats
        └── GET    /
"""