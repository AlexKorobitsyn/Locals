from concurrent.futures import ThreadPoolExecutor

import pytest
from test_admin_experience import city, credit_listen, playable, set_role
from test_library import music as music
from test_library import rate, result

pytestmark = pytest.mark.integration


def proposal(client, headers, track_id, text="A community version"):
    return result(
        client.post(
            "/api/v1/contributions",
            headers=headers,
            json={
                "target_type": "track",
                "target_id": track_id,
                "field": "lyrics",
                "lyrics": text,
            },
        ),
        201,
    )


def voters(account, database, count=5):
    values = []
    for index in range(count):
        user, headers = account(f"voter{index}")
        set_role(database, user, "experienced", 100)
        values.append((user, headers))
    return values


def progress(client, headers):
    return result(client.get("/api/v1/me/experience", headers=headers))


def test_everyone_proposes_limits_duplicates_and_withdrawal(
    api_client, account, catalog_db, music
):
    _, _, _, _, tracks = music
    user, headers = account("newcomer")
    first = proposal(api_client, headers, tracks[0]["id"])
    assert progress(api_client, headers)["experience_level"] == 1
    assert progress(api_client, headers)["contribution_limit"] == 2
    assert (
        api_client.post(
            "/api/v1/contributions",
            headers=headers,
            json={
                "target_type": "track",
                "target_id": tracks[0]["id"],
                "field": "lyrics",
                "lyrics": "Duplicate",
            },
        ).status_code
        == 409
    )
    second = proposal(api_client, headers, tracks[1]["id"])
    assert (
        api_client.post(
            "/api/v1/contributions",
            headers=headers,
            json={
                "target_type": "track",
                "target_id": tracks[2]["id"],
                "field": "lyrics",
                "lyrics": "Limit",
            },
        ).status_code
        == 409
    )
    assert result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"] is None
    result(
        api_client.delete(f"/api/v1/contributions/{second['id']}", headers=headers), 204
    )
    proposal(api_client, headers, tracks[2]["id"])
    assert progress(api_client, headers)["experience_points"] == 0
    _, foreign = account("foreign")
    assert (
        api_client.delete(
            f"/api/v1/contributions/{first['id']}", headers=foreign
        ).status_code
        == 403
    )
    assert (
        result(api_client.get("/api/v1/contributions", headers=foreign))["total"] == 2
    )


def test_community_votes_are_unique_and_concurrent_acceptance_awards_once(
    api_client, account, catalog_db, music
):
    _, _, _, _, tracks = music
    author, headers = account("contributor")
    entry = proposal(api_client, headers, tracks[0]["id"])
    assert (
        api_client.put(
            f"/api/v1/contributions/{entry['id']}/vote", headers=headers
        ).status_code
        == 403
    )
    _, newcomer = account("newcomer")
    outcome = result(
        api_client.put(f"/api/v1/contributions/{entry['id']}/vote", headers=newcomer)
    )
    assert outcome["votes_count"] == 1 and outcome["eligible_votes_count"] == 0
    eligible = voters(account, catalog_db)
    # Повтор одного голоса не увеличивает счётчик.
    for _ in range(2):
        outcome = result(
            api_client.put(
                f"/api/v1/contributions/{entry['id']}/vote", headers=eligible[0][1]
            )
        )
    assert outcome["votes_count"] == 2 and outcome["eligible_votes_count"] == 1

    def cast(pair):
        return api_client.put(
            f"/api/v1/contributions/{entry['id']}/vote", headers=pair[1]
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(
            response.status_code == 200 for response in pool.map(cast, eligible[1:])
        )
    assert (
        result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"]
        == "A community version"
    )
    assert progress(api_client, headers)["experience_points"] == 20
    assert (
        api_client.put(
            f"/api/v1/contributions/{entry['id']}/vote", headers=eligible[0][1]
        ).status_code
        == 409
    )
    assert (
        len(
            catalog_db.execute(
                "SELECT id FROM experience_awards WHERE user_id=:id AND kind='contribution'",
                {"id": author["id"]},
            )
        )
        == 1
    )


def test_owner_version_cannot_be_replaced_by_votes_or_moderator(
    api_client, account, catalog_db, music
):
    _, own, _, _, tracks = music
    result(
        api_client.patch(
            f"/api/v1/tracks/{tracks[0]['id']}",
            headers=own,
            json={"lyrics": "Owner version"},
        )
    )
    _, headers = account("contributor")
    entry = proposal(api_client, headers, tracks[0]["id"])
    for _, voter in voters(account, catalog_db):
        outcome = result(
            api_client.put(f"/api/v1/contributions/{entry['id']}/vote", headers=voter)
        )
    assert outcome["status"] == "pending" and outcome["requires_owner"]
    mod, moderation = account("mod")
    set_role(catalog_db, mod, "moderator")
    assert (
        api_client.put(
            f"/api/v1/admin/contributions/{entry['id']}",
            headers=moderation,
            json={"decision": "approve"},
        ).status_code
        == 403
    )
    assert (
        result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"]
        == "Owner version"
    )
    result(
        api_client.put(
            f"/api/v1/contributions/{entry['id']}/review",
            headers=own,
            json={"decision": "approve"},
        )
    )
    assert progress(api_client, headers)["experience_points"] == 20
    assert (
        result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"]
        == "A community version"
    )


def test_venue_pending_visibility_review_award_and_event_limits(
    api_client, account, catalog_db
):
    user, headers = account("organizer")
    city_id = city(catalog_db)
    venue = result(
        api_client.post(
            "/api/v1/venues",
            headers=headers,
            json={
                "name": "Local club",
                "city_id": city_id,
                "lat": 56,
                "lng": 60,
                "address": "Main Street 1",
            },
        ),
        201,
    )
    assert venue["publication_status"] == "pending"
    assert result(api_client.get("/api/v1/venues"))["total"] == 0
    assert api_client.get(f"/api/v1/venues/{venue['id']}").status_code == 404
    assert (
        api_client.put(
            "/api/v1/ratings",
            headers=headers,
            json={"target_type": "venue", "target_id": venue["id"], "value": 5},
        ).status_code
        == 404
    )
    entry = result(api_client.get("/api/v1/contributions", headers=headers))["items"][0]
    assert entry["proposed"]["address"] == "Main Street 1"
    for _, voter in voters(account, catalog_db):
        result(
            api_client.put(f"/api/v1/contributions/{entry['id']}/vote", headers=voter)
        )
    assert result(api_client.get("/api/v1/venues"))["total"] == 1
    assert progress(api_client, headers)["experience_points"] == 40
    catalog_db.execute(
        "UPDATE users SET scene_verified=true WHERE id=:id", {"id": user["id"]}
    )
    for index in range(5):
        event = result(
            api_client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "name": f"Event {index}",
                    "venue_id": venue["id"],
                    "starts_at": "2099-01-01T20:00:00Z",
                },
            ),
            201,
        )
        assert event["publication_status"] == "published"
    assert (
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Too many",
                "venue_id": venue["id"],
                "starts_at": "2099-01-01T20:00:00Z",
            },
        ).status_code
        == 409
    )
    set_role(catalog_db, user, "experienced", 25000)
    assert progress(api_client, headers)["experience_level"] == 9
    assert progress(api_client, headers)["event_limit"] == 20
    result(
        api_client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "name": "Legend event",
                "venue_id": venue["id"],
                "starts_at": "2099-01-01T20:00:00Z",
            },
        ),
        201,
    )


def test_reviews_micro_rewards_do_not_farm_on_recreation(
    api_client, account, catalog_db, music
):
    _, _, artist, _, tracks = music
    user, headers = account("critic")
    rate(api_client, headers, tracks[0]["id"])
    short = result(
        api_client.post(
            "/api/v1/reviews",
            headers=headers,
            json={
                "target_type": "track",
                "target_id": tracks[0]["id"],
                "text": "Short review",
            },
        ),
        201,
    )
    assert progress(api_client, headers)["experience_points"] == 1
    text = "A thoughtful analysis of this track and its arrangement. " * 6
    result(
        api_client.patch(
            f"/api/v1/reviews/{short['id']}", headers=headers, json={"text": text}
        )
    )
    assert progress(api_client, headers)["experience_points"] == 21
    result(api_client.delete(f"/api/v1/reviews/{short['id']}", headers=headers), 204)
    result(
        api_client.post(
            "/api/v1/reviews",
            headers=headers,
            json={"target_type": "track", "target_id": tracks[0]["id"], "text": text},
        ),
        201,
    )
    for _ in range(2):
        result(
            api_client.delete(
                f"/api/v1/ratings/track/{tracks[0]['id']}", headers=headers
            ),
        )
        rate(api_client, headers, tracks[0]["id"])
    assert progress(api_client, headers)["experience_points"] == 21
    rate(api_client, headers, tracks[1]["id"])
    result(
        api_client.post(
            "/api/v1/reviews",
            headers=headers,
            json={"target_type": "track", "target_id": tracks[1]["id"], "text": text},
        ),
        201,
    )
    assert progress(api_client, headers)["experience_points"] == 22
    for _ in range(2):
        result(
            api_client.put(
                "/api/v1/follows",
                headers=headers,
                json={"target_type": "artist", "target_id": artist["id"]},
            )
        )
        result(
            api_client.delete(
                f"/api/v1/follows/artist/{artist['id']}", headers=headers
            ),
            204,
        )
    assert progress(api_client, headers)["experience_points"] == 23
    playlist = result(
        api_client.post(
            "/api/v1/playlists", headers=headers, json={"name": "Discovery"}
        ),
        201,
    )
    for _ in range(2):
        result(
            api_client.post(
                f"/api/v1/playlists/{playlist['id']}/tracks",
                headers=headers,
                json={"track_id": tracks[2]["id"]},
            ),
            204,
        )
        result(
            api_client.delete(
                f"/api/v1/playlists/{playlist['id']}/tracks/{tracks[2]['id']}",
                headers=headers,
            ),
            204,
        )
    assert progress(api_client, headers)["experience_points"] == 24
    history = result(api_client.get("/api/v1/me/experience/awards", headers=headers))
    assert sum(item["points"] for item in history["items"]) == 24


def test_listening_pause_auto_level_and_publication_reward(
    api_client, account, catalog_db, music
):
    owner, own, _, _, tracks = music
    playable(catalog_db, owner, tracks[0], 20)
    user, headers = account("listenerxp")
    set_role(catalog_db, user, "green", 99)
    outcome = credit_listen(api_client, catalog_db, headers, tracks[0]["id"])
    assert outcome["experience"]["experience_level"] == 2
    assert (
        result(api_client.get("/api/v1/me", headers=headers))["level"] == "experienced"
    )
    result(api_client.post("/api/v1/me/experience/claim", headers=own))
    assert progress(api_client, own)["experience_points"] == 10
    result(api_client.post("/api/v1/me/experience/claim", headers=own))
    assert progress(api_client, own)["experience_points"] == 10
    listening = result(
        api_client.post(f"/api/v1/tracks/{tracks[0]['id']}/listening", headers=headers),
        201,
    )
    result(
        api_client.put(
            f"/api/v1/listening/{listening['id']}",
            headers=headers,
            json={"is_playing": False},
        )
    )
    catalog_db.execute(
        "UPDATE listening_sessions SET last_seen_at=CURRENT_TIMESTAMP-interval '1 hour' WHERE id=:id",
        {"id": listening["id"]},
    )
    paused = result(
        api_client.put(
            f"/api/v1/listening/{listening['id']}",
            headers=headers,
            json={"is_playing": False},
        )
    )
    assert paused["seconds"] < 1 and not paused["awarded"]


def test_manual_levels_scene_verification_and_community_awards(
    api_client, account, catalog_db
):
    admin, headers = account("admin")
    target, _ = account("organizer")
    set_role(catalog_db, admin, "admin")
    granted = result(
        api_client.put(
            f"/api/v1/admin/users/{target['id']}/experience",
            headers=headers,
            json={"tier": 8},
        )
    )
    assert granted["experience_points"] == 25000 and granted["scene_verified"]
    assert granted["level"] == "experienced"
    assert (
        api_client.put(
            f"/api/v1/admin/users/{target['id']}/level",
            headers=headers,
            json={"level": "admin"},
        ).status_code
        == 422
    )
    for _ in range(2):
        result(
            api_client.post(
                f"/api/v1/admin/users/{target['id']}/community-awards",
                headers=headers,
                json={"kind": "curator_week", "period": "2026-01-05"},
            )
        )
    assert (
        catalog_db.execute(
            "SELECT experience_points FROM users WHERE id=:id", {"id": target["id"]}
        )[0]["experience_points"]
        == 25100
    )
    other, _ = account("other")
    assert (
        api_client.post(
            f"/api/v1/admin/users/{other['id']}/community-awards",
            headers=headers,
            json={"kind": "curator_week", "period": "2026-01-05"},
        ).status_code
        == 409
    )
    assert (
        api_client.post(
            f"/api/v1/admin/users/{other['id']}/community-awards",
            headers=headers,
            json={"kind": "curator_week", "period": "2026-01-06"},
        ).status_code
        == 422
    )


def test_stale_proposal_never_overwrites_updated_catalog(
    api_client, account, catalog_db, music
):
    _, _, _, _, tracks = music
    _, headers = account("contributor")
    entry = proposal(api_client, headers, tracks[0]["id"])
    mod, moderation = account("moderator")
    set_role(catalog_db, mod, "moderator")
    result(
        api_client.patch(
            f"/api/v1/tracks/{tracks[0]['id']}",
            headers=moderation,
            json={"lyrics": "New moderator version"},
        )
    )
    for _, voter in voters(account, catalog_db):
        outcome = result(
            api_client.put(f"/api/v1/contributions/{entry['id']}/vote", headers=voter)
        )
    assert outcome["status"] == "pending"
    assert (
        result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"]
        == "New moderator version"
    )
    assert (
        api_client.put(
            f"/api/v1/admin/contributions/{entry['id']}",
            headers=moderation,
            json={"decision": "approve"},
        ).status_code
        == 409
    )


def test_milestones_and_past_month_venue_bonus_are_claimed_once(
    api_client, account, catalog_db, music
):
    from datetime import UTC, datetime, timedelta

    owner, own, _, _, tracks = music
    playable(catalog_db, owner, tracks[0], 20)
    cohort = catalog_db.execute(
        "INSERT INTO users(email,display_name,password_hash) SELECT 'audience-'||n||'@example.com','Audience '||n,'fixture-only-hash' FROM generate_series(1,100) n RETURNING id"
    )
    audience = [row["id"] for row in cohort]
    catalog_db.execute(
        "INSERT INTO listening_sessions(id,user_id,track_id,last_seen_at,expires_at,ended_at,is_playing,seconds,required_seconds) SELECT gen_random_uuid(),uid,:track,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP+interval '1 hour',CURRENT_TIMESTAMP,false,19,19 FROM unnest(CAST(:ids AS integer[])) uid",
        {"track": tracks[0]["id"], "ids": audience},
    )
    other, other_headers = account("otherauthor")
    artist = result(
        api_client.post(
            "/api/v1/artists", headers=other_headers, json={"name": "Foreign artist"}
        ),
        201,
    )
    foreign = result(
        api_client.post(
            "/api/v1/tracks",
            headers=other_headers,
            json={
                "title": "Foreign song",
                "duration": 20,
                "artist_ids": [artist["id"]],
            },
        ),
        201,
    )
    rate(api_client, own, foreign["id"])
    review = result(
        api_client.post(
            "/api/v1/reviews",
            headers=own,
            json={
                "target_type": "track",
                "target_id": foreign["id"],
                "text": "Thoughtful musical analysis and observations about the melody. "
                * 7,
            },
        ),
        201,
    )
    catalog_db.execute(
        "INSERT INTO favorites(user_id,entity_type,entity_id,review_id) SELECT uid,'review',:review,:review FROM unnest(CAST(:ids AS integer[])) uid",
        {"review": review["id"], "ids": audience[:10]},
    )
    catalog_db.execute(
        "UPDATE users SET scene_verified=true WHERE id=:id", {"id": owner["id"]}
    )
    venue = result(
        api_client.post(
            "/api/v1/venues",
            headers=own,
            json={
                "name": "Active club",
                "city_id": city(catalog_db),
                "lat": 56,
                "lng": 60,
            },
        ),
        201,
    )
    month = (datetime.now(UTC).replace(day=1) - timedelta(days=1)).replace(
        day=1, hour=18, minute=0, second=0, microsecond=0
    )
    for index in range(5):
        starts = month + timedelta(days=index)
        event = result(
            api_client.post(
                "/api/v1/events",
                headers=own,
                json={
                    "name": f"Past live show {index}",
                    "venue_id": venue["id"],
                    "starts_at": starts.isoformat(),
                    "stop_at": (starts + timedelta(hours=2)).isoformat(),
                },
            ),
            201,
        )
        catalog_db.execute(
            "INSERT INTO event_attendance(event_id,user_id) SELECT :event,uid FROM unnest(CAST(:ids AS integer[])) uid",
            {"event": event["id"], "ids": audience[:20]},
        )
    first = result(api_client.post("/api/v1/me/experience/claim", headers=own))
    second = result(api_client.post("/api/v1/me/experience/claim", headers=own))
    assert first["experience_points"] == second["experience_points"]
    by_kind = {
        row["kind"]: row["count"]
        for row in catalog_db.execute(
            "SELECT kind,count(*) FROM experience_awards WHERE user_id=:id GROUP BY kind",
            {"id": owner["id"]},
        )
    }
    assert (
        by_kind["track_audience"]
        == by_kind["review_likes"]
        == by_kind["publication"]
        == by_kind["venue_month"]
        == 1
    )
    assert by_kind["event_audience"] == 5


def test_meaningful_streak_doubles_only_today_listening(
    api_client, account, catalog_db, music
):
    from datetime import UTC, datetime, timedelta

    owner, _, _, _, tracks = music
    playable(catalog_db, owner, tracks[0], 20)
    user, headers = account("streaklistener")
    today = datetime.now(UTC).date()
    for delta in range(1, 7):
        day = today - timedelta(days=delta)
        catalog_db.execute(
            "INSERT INTO experience_awards(user_id,track_id,source_key,kind,day,points) VALUES (:user,:track,:key,'listen',:day,1)",
            {
                "user": user["id"],
                "track": tracks[0]["id"],
                "key": f"listen:{tracks[0]['id']}:{day}",
                "day": day,
            },
        )
    catalog_db.execute(
        "UPDATE users SET experience_points=6 WHERE id=:id", {"id": user["id"]}
    )
    credit_listen(api_client, catalog_db, headers, tracks[0]["id"])
    assert progress(api_client, headers)["experience_points"] == 7
    for _ in range(2):
        result(api_client.post("/api/v1/me/experience/claim", headers=headers))
    assert progress(api_client, headers)["experience_points"] == 8
    assert (
        len(catalog_db.execute("SELECT id FROM experience_awards WHERE kind='streak'"))
        == 1
    )


def test_proposal_xp_and_content_roll_back_if_audit_fails(
    api_client, account, catalog_db, music
):
    from sqlalchemy.exc import IntegrityError

    _, _, _, _, tracks = music
    user, headers = account("helper")
    mod, moderation = account("staff")
    set_role(catalog_db, mod, "moderator")
    entry = proposal(api_client, headers, tracks[0]["id"])
    catalog_db.execute(
        "ALTER TABLE event_logs ADD CONSTRAINT fail_xp_audit CHECK (action <> 'experience_awarded')"
    )
    with pytest.raises(IntegrityError):
        api_client.put(
            f"/api/v1/admin/contributions/{entry['id']}",
            headers=moderation,
            json={"decision": "approve"},
        )
    assert progress(api_client, headers)["experience_points"] == 0
    assert result(api_client.get(f"/api/v1/tracks/{tracks[0]['id']}"))["lyrics"] is None
    assert (
        catalog_db.execute(
            "SELECT status FROM contributions WHERE id=:id", {"id": entry["id"]}
        )[0]["status"]
        == "pending"
    )
    assert (
        catalog_db.execute(
            "SELECT id FROM experience_awards WHERE user_id=:id", {"id": user["id"]}
        )
        == []
    )
