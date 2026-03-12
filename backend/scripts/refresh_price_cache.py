from db import SessionLocal, init_db
from services.etf_cache import SUPPORTED_ETFS
from services.price_cache import refresh_price_cache


def main() -> None:
    init_db()
    with SessionLocal() as session:
        for ticker in SUPPORTED_ETFS:
            result = refresh_price_cache(session, ticker=ticker)
            print(
                f"{result.ticker} updated={result.updated} "
                f"price={result.price} "
                f"price_date={result.price_date} "
                f"fetched_at={result.fetched_at}"
            )


if __name__ == "__main__":
    main()
