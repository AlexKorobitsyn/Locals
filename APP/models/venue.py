class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None]
    cover_url: Mapped[str | None]

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    address: Mapped[str | None]
    lat: Mapped[float]
    lng: Mapped[float]

    capacity: Mapped[int | None]        # сколько влезает
    website: Mapped[str | None]

    # оценка — центральная, как у альбомов
    rating_sum: Mapped[float] = mapped_column(default=0.0)
    rating_weight: Mapped[float] = mapped_column(default=0.0)
    ratings_count: Mapped[int] = mapped_column(default=0)