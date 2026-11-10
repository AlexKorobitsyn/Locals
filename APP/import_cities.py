"""Одноразовый импорт справочника GeoNames: python -m APP.import_cities."""

import argparse
import asyncio
import csv
import io
import logging
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zipfile import ZipFile

from sqlalchemy import func, select

from APP.core.config import get_settings
from APP.core.db import create_engine, create_session_factory
from APP.core.logging import configure_logging
from APP.models.city import City
from APP.schemas.city import CityCreate

logger = logging.getLogger(__name__)
CITIES_ARCHIVE = "cities1000.zip"
ADMIN_FILE = "admin1CodesASCII.txt"
CITY_CODES = frozenset({"PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"})
IMPORT_LOCK = "locals:geonames:cities"
COUNTRY_PATTERN = re.compile(r"[A-Z]{2}")
RU_COUNTRY_ALIASES = frozenset(
    {"ru", "rus", "russia", "россия", "российская федерация"}
)


def country_code(value):
    value = value.strip().upper()
    if not COUNTRY_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "Use a two-letter country code, for example RU"
        )
    return value


def fetch_file(settings, directory, remote, filename, refresh=False):
    path = directory / filename
    if path.exists() and not refresh:
        return path
    request = Request(
        urljoin(str(settings.geonames_base_url).rstrip("/") + "/", remote),
        headers={"User-Agent": "Locals GeoNames importer"},
    )
    temporary = None
    try:
        with urlopen(
            request, timeout=settings.geonames_download_timeout_seconds
        ) as response:
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as output:
                temporary = Path(output.name)
                shutil.copyfileobj(response, output)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    logger.info("GeoNames file downloaded", extra={"source_file": filename})
    return path


def zip_rows(path, member):
    with ZipFile(path) as archive:
        with archive.open(member) as source:
            yield from csv.reader(
                io.TextIOWrapper(source, encoding="utf-8"),
                delimiter="\t",
                quoting=csv.QUOTE_NONE,
            )


def localized_names(path, member, wanted_ids, language):
    selected = {}
    for row in zip_rows(path, member):
        if len(row) < 4 or row[2] != language or int(row[1]) not in wanted_ids:
            continue
        fields = row + [""] * max(0, 8 - len(row))
        if fields[6] == "1" or fields[7] == "1":
            continue
        name = row[3].strip()
        if not name:
            continue
        rank = (fields[4] == "1", fields[5] != "1", name)
        geoname_id = int(row[1])
        if geoname_id not in selected or rank > selected[geoname_id][0]:
            selected[geoname_id] = (rank, name)
    return {key: value[1] for key, value in selected.items()}


def load_cities(directory, countries, language="ru"):
    with (directory / ADMIN_FILE).open(encoding="utf-8") as source:
        regions = {
            row[0]: (int(row[3]), row[1])
            for row in csv.reader(source, delimiter="\t", quoting=csv.QUOTE_NONE)
            if len(row) >= 4 and row[0].split(".")[0] in countries
        }
    rows = [
        row
        for row in zip_rows(directory / CITIES_ARCHIVE, "cities1000.txt")
        if len(row) >= 19
        and row[8] in countries
        and row[6] == "P"
        and row[7] in CITY_CODES
    ]
    wanted_ids = {int(row[0]) for row in rows} | {
        value[0] for value in regions.values()
    }
    names = {}
    for country in sorted(countries):
        names.update(
            localized_names(
                directory / f"alternate-names-{country}.zip",
                f"{country}.txt",
                wanted_ids,
                language,
            )
        )
    cities = {}
    for row in rows:
        geoname_id = int(row[0])
        region = regions.get(f"{row[8]}.{row[10]}")
        region_name = names.get(region[0], region[1]) if region else None
        if region_name:
            for suffix in (
                " Автономная Область",
                " Автономный Округ",
                " Область",
                " Край",
            ):
                region_name = region_name.replace(suffix, suffix.lower())
        payload = CityCreate(
            name=names.get(geoname_id, row[1]),
            region=region_name,
            country=row[8],
            lat=float(row[4]),
            lng=float(row[5]),
            timezone=row[17],
        ).model_dump()
        cities[geoname_id] = {"geoname_id": geoname_id, **payload}
    if not cities:
        raise ValueError("No cities matched the selected countries")
    return list(cities.values())


def identity(row):
    country = row["country"].strip().casefold()
    if country in RU_COUNTRY_ALIASES:
        country = "ru"

    def normalize(value):
        return (value or "").strip().casefold().replace("ё", "е")

    return normalize(row["name"]), normalize(row["region"]), country


async def import_cities(session, cities):
    result = {"created": 0, "updated": 0, "matched_manual": 0, "unchanged": 0}
    source_counts = Counter(identity(row) for row in cities)
    async with session.begin():
        # Два импорта не должны одновременно привязывать одну ручную запись.
        await session.execute(
            select(func.pg_advisory_xact_lock(func.hashtext(IMPORT_LOCK)))
        )
        existing = list((await session.scalars(select(City))).all())
        by_geoname = {
            city.geoname_id: city for city in existing if city.geoname_id is not None
        }
        manual = defaultdict(list)
        for city in existing:
            if city.geoname_id is None:
                manual[
                    identity(
                        {
                            key: getattr(city, key)
                            for key in ("name", "region", "country")
                        }
                    )
                ].append(city)
        for row in cities:
            city = by_geoname.get(row["geoname_id"])
            if city is None:
                candidates = manual.get(identity(row), [])
                if len(candidates) == 1 and source_counts[identity(row)] == 1:
                    city = candidates.pop()
                    result["matched_manual"] += 1
                else:
                    city = City(**row)
                    session.add(city)
                    result["created"] += 1
                    continue
            changed = any(getattr(city, key) != value for key, value in row.items())
            for key, value in row.items():
                setattr(city, key, value)
            result["updated" if changed else "unchanged"] += 1
    return result


async def store_cities(settings, cities):
    engine = create_engine(settings)
    try:
        async with create_session_factory(engine)() as session:
            return await import_cities(session, cities)
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--country",
        action="append",
        type=country_code,
        help="ISO code; default RU; repeat for multiple countries",
    )
    parser.add_argument(
        "--language", default="ru", help="Preferred name language; default ru"
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path(tempfile.gettempdir()) / "locals-geonames"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="Download a fresh dataset"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download and validate without database writes",
    )
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    countries = set(args.country or ["RU"])
    args.data_dir.mkdir(parents=True, exist_ok=True)
    fetch_file(settings, args.data_dir, CITIES_ARCHIVE, CITIES_ARCHIVE, args.refresh)
    fetch_file(settings, args.data_dir, ADMIN_FILE, ADMIN_FILE, args.refresh)
    for country in sorted(countries):
        fetch_file(
            settings,
            args.data_dir,
            f"alternatenames/{country}.zip",
            f"alternate-names-{country}.zip",
            args.refresh,
        )
    cities = load_cities(args.data_dir, countries, args.language)
    logger.info(
        "GeoNames data validated",
        extra={"cities_count": len(cities), "countries": sorted(countries)},
    )
    if not args.dry_run:
        result = asyncio.run(store_cities(settings, cities))
        logger.info("GeoNames cities imported", extra={"import_result": result})


if __name__ == "__main__":
    main()
