from db import SessionLocal, init_db
from services.etf_cache import SUPPORTED_ETFS, refresh_etf_cache


def main() -> None:
    init_db()
    with SessionLocal() as session:
        for ticker in SUPPORTED_ETFS:
            result = refresh_etf_cache(session, ticker=ticker)
            print(
                f"{result.ticker} updated={result.updated} "
                f"holdings_count={result.holdings_count} "
                f"data_as_of={result.data_as_of_date} "
                f"last_refreshed_at={result.last_refreshed_at}"
            )


if __name__ == "__main__":
    main()
