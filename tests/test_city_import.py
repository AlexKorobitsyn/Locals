import asyncio
import io
import json
from zipfile import ZipFile

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker

from APP.import_cities import import_cities, load_cities


def dataset(directory, timezone="Asia/Yekaterinburg"):
    row = [
        "1001",
        "Yekaterinburg",
        "Yekaterinburg",
        "",
        "56.84",
        "60.61",
        "P",
        "PPLA",
        "RU",
        "",
        "71",
        "",
        "",
        "",
        "1500000",
        "",
        "",
        timezone,
        "2026-11-10",
    ]
    district = [*row]
    district[0], district[7] = "1002", "PPLX"
    with ZipFile(directory / "cities1000.zip", "w") as archive:
        archive.writestr(
            "cities1000.txt", "\t".join(row) + "\n" + "\t".join(district) + "\n"
        )
    (directory / "admin1CodesASCII.txt").write_text(
        "RU.71\tSverdlovsk\tSverdlovsk\t2001\n"
    )
    with ZipFile(directory / "alternate-names-RU.zip", "w") as archive:
        archive.writestr(
            "RU.txt",
            "1\t1001\tru\tЕкатеринбург\t1\t\t\t\n"
            "2\t1001\tru\tСвердловск\t\t\t\t1\n"
            "3\t1001\ten\tEkaterinburg\t1\t\t\t\n"
            "4\t2001\tru\tСвердловская Область\t1\t\t\t\n",
        )


def test_reads_localized_names_region_coordinates_and_timezone(tmp_path):
    dataset(tmp_path)
    assert load_cities(tmp_path, {"RU"}) == [
        {
            "geoname_id": 1001,
            "name": "Екатеринбург",
            "region": "Свердловская область",
            "country": "RU",
            "lat": 56.84,
            "lng": 60.61,
            "timezone": "Asia/Yekaterinburg",
        }
    ]


def test_rejects_unknown_timezone_before_import(tmp_path):
    dataset(tmp_path, timezone="Not/A_Timezone")
    with pytest.raises(ValidationError, match="unknown IANA timezone"):
        load_cities(tmp_path, {"RU"})


def test_download_writes_file_and_logs_without_reserved_fields(
    tmp_path, monkeypatch, capsys, settings
):
    import APP.import_cities as module
    from APP.core.logging import configure_logging

    configure_logging("INFO")
    monkeypatch.setattr(
        module, "urlopen", lambda *args, **kwargs: io.BytesIO(b"dataset")
    )
    path = module.fetch_file(settings, tmp_path, "cities1000.zip", "cities1000.zip")
    assert path.read_bytes() == b"dataset"
    assert json.loads(capsys.readouterr().out)["source_file"] == "cities1000.zip"


def test_cli_logs_result_without_overwriting_logging_fields(
    tmp_path, monkeypatch, capsys, settings
):
    import APP.import_cities as module

    dataset(tmp_path)
    result = {"created": 1, "updated": 0, "matched_manual": 0, "unchanged": 0}

    async def store(*_):
        return result

    monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(module, "store_cities", store)
    monkeypatch.setattr(module, "fetch_file", lambda *args: None)
    monkeypatch.setattr("sys.argv", ["import_cities", "--data-dir", str(tmp_path)])
    module.main()
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert lines[-1]["import_result"] == result


def run_import(database, cities):
    async def run():
        async with async_sessionmaker(
            database.engine, expire_on_commit=False
        )() as session:
            return await import_cities(session, cities)

    return asyncio.run(run())


@pytest.mark.integration
def test_matches_manual_city_preserves_references_and_updates_by_geoname(catalog_db):
    old = catalog_db.execute(
        "INSERT INTO cities(name,region,country,lat,lng,timezone) VALUES "
        "('Екатеринбург','Свердловская область','Россия',56,60,'Asia/Yekaterinburg') RETURNING id"
    )[0]["id"]
    artist = catalog_db.execute(
        "INSERT INTO artists(name,city_id) VALUES ('Existing artist',:city) RETURNING id",
        {"city": old},
    )[0]["id"]
    city = {
        "geoname_id": 1001,
        "name": "Екатеринбург",
        "region": "Свердловская область",
        "country": "RU",
        "lat": 56.84,
        "lng": 60.61,
        "timezone": "Asia/Yekaterinburg",
    }
    first = run_import(catalog_db, [city])
    assert first["matched_manual"] == 1 and first["created"] == 0
    renamed = {**city, "name": "Новое название", "lat": 56.85}
    assert run_import(catalog_db, [renamed])["updated"] == 1
    assert run_import(catalog_db, [renamed])["unchanged"] == 1
    rows = catalog_db.execute("SELECT id,name,geoname_id FROM cities")
    assert len(rows) == 1
    assert dict(rows[0]) == {"id": old, "name": "Новое название", "geoname_id": 1001}
    assert (
        catalog_db.execute("SELECT city_id FROM artists WHERE id=:id", {"id": artist})[
            0
        ]["city_id"]
        == old
    )


@pytest.mark.integration
def test_distinct_places_with_same_name_are_not_merged(catalog_db):
    city = {
        "name": "Берёзовка",
        "region": "Красноярский край",
        "country": "RU",
        "lat": 56.2,
        "lng": 93.1,
        "timezone": "Asia/Krasnoyarsk",
    }
    cities = [{**city, "geoname_id": 1001}, {**city, "geoname_id": 1002, "lat": 57.1}]
    assert run_import(catalog_db, cities)["created"] == 2
    assert run_import(catalog_db, cities)["unchanged"] == 2
    assert catalog_db.execute("SELECT count(*) AS total FROM cities")[0]["total"] == 2


@pytest.mark.integration
def test_imported_city_is_searchable_and_manual_duplicate_is_rejected(
    api_client, catalog_db, account
):
    city = {
        "geoname_id": 1001,
        "name": "Екатеринбург",
        "region": "Свердловская область",
        "country": "RU",
        "lat": 56.84,
        "lng": 60.61,
        "timezone": "Asia/Yekaterinburg",
    }
    run_import(catalog_db, [city])
    response = api_client.get("/api/v1/cities", params={"q": "катерин", "limit": 1})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["region"] == city["region"]
    user, headers = account("city-moderator")
    catalog_db.execute(
        "UPDATE users SET level='moderator' WHERE id=:id", {"id": user["id"]}
    )
    payload = {key: value for key, value in city.items() if key != "geoname_id"}
    assert (
        api_client.post("/api/v1/cities", json=payload, headers=headers).status_code
        == 409
    )
