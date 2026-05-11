import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from memory.audit_log import engine, Watchlist, AssetUniverse


def _display_name(name: str, symbol: str) -> str:
    n = (name or "").strip()
    return n if n else symbol.upper()

def get_watchlist() -> list[dict]:
    """Returns all active watchlist assets."""
    with Session(engine) as session:
        items = session.query(Watchlist, AssetUniverse).join(
            AssetUniverse,
            Watchlist.symbol == AssetUniverse.symbol
        ).filter(Watchlist.is_active == True).all()
        return [
            {
                "symbol":      w.symbol,
                "name":        a.name,
                "asset_type":  a.asset_type,
                "coingecko_id": a.coingecko_id,
                "added_at":    str(w.added_at),
                "is_active":   w.is_active,
            }
            for w, a in items
        ]


def get_all_assets() -> list[dict]:
    """Returns all assets in the universe — watchlisted or not."""
    with Session(engine) as session:
        assets = session.query(AssetUniverse)\
            .filter(AssetUniverse.is_active == True).all()
        watchlisted = {
            w.symbol for w in
            session.query(Watchlist)
            .filter(Watchlist.is_active == True).all()
        }
        return [
            {
                "symbol":       a.symbol,
                "name":         a.name,
                "asset_type":   a.asset_type,
                "coingecko_id": a.coingecko_id,
                "in_watchlist": a.symbol in watchlisted,
            }
            for a in assets
        ]


def add_to_watchlist(symbol: str) -> dict:
    """Adds an asset to the watchlist."""
    with Session(engine) as session:
        # check asset exists in universe
        asset = session.query(AssetUniverse)\
            .filter(
                AssetUniverse.symbol == symbol.upper(),
                AssetUniverse.is_active == True,
            ).first()
        if not asset:
            return {"success": False, "reason": f"{symbol} not in asset universe"}

        # check if already in watchlist
        existing = session.query(Watchlist).filter(
            Watchlist.symbol == symbol.upper()
        ).first()

        if existing:
            if existing.is_active:
                return {"success": False, "reason": f"{symbol} already in watchlist"}
            else:
                existing.is_active = True
                existing.added_at  = datetime.utcnow()
                session.commit()
                return {"success": True, "reason": f"{symbol} re-activated"}

        session.add(Watchlist(symbol=symbol.upper(), is_active=True))
        session.commit()
        return {"success": True, "reason": f"{symbol} added to watchlist"}


def remove_from_watchlist(symbol: str) -> dict:
    """Removes an asset from the watchlist."""
    with Session(engine) as session:
        item = session.query(Watchlist).filter(
            Watchlist.symbol == symbol.upper(),
            Watchlist.is_active == True
        ).first()
        if not item:
            return {"success": False, "reason": f"{symbol} not in watchlist"}
        item.is_active = False
        session.commit()
        return {"success": True, "reason": f"{symbol} removed from watchlist"}


def add_new_asset(
    symbol: str,
    name: str,
    asset_type: str,
    coingecko_id: str = None,
) -> dict:
    """
    Adds a completely new asset to the universe.
    Use this to add assets beyond the default 7.
    """
    with Session(engine) as session:
        existing = session.query(AssetUniverse)\
            .filter(AssetUniverse.symbol == symbol.upper()).first()
        if existing:
            if existing.is_active:
                return {"success": False, "reason": f"{symbol} already exists"}
            existing.name = _display_name(name, symbol)
            existing.asset_type = asset_type
            existing.coingecko_id = coingecko_id
            existing.is_active = True
            existing.added_at = datetime.utcnow()
            session.commit()
            return {"success": True, "reason": f"{symbol} restored to universe"}

        session.add(AssetUniverse(
            symbol=symbol.upper(),
            name=_display_name(name, symbol),
            asset_type=asset_type,
            coingecko_id=coingecko_id,
        ))
        session.commit()
        return {"success": True, "reason": f"{symbol} added to universe"}


def update_asset(
    symbol: str,
    name: str,
    asset_type: str,
    coingecko_id: str = None,
) -> dict:
    """Update name, type, and CoinGecko id. Symbol (primary key) cannot change."""
    with Session(engine) as session:
        asset = session.query(AssetUniverse).filter(
            AssetUniverse.symbol == symbol.upper(),
            AssetUniverse.is_active == True,
        ).first()
        if not asset:
            return {"success": False, "reason": "Asset not found or inactive"}
        asset.name = _display_name(name, symbol)
        asset.asset_type = asset_type
        asset.coingecko_id = (coingecko_id or "").strip() or None
        session.commit()
        return {"success": True, "reason": f"{symbol.upper()} updated"}


def deactivate_asset(symbol: str) -> dict:
    """
    Soft-remove from universe: hide from listings and take off watchlist.
    Keeps DB row for foreign keys (positions, alerts history).
    """
    with Session(engine) as session:
        asset = session.query(AssetUniverse).filter(
            AssetUniverse.symbol == symbol.upper(),
        ).first()
        if not asset:
            return {"success": False, "reason": "Asset not found"}
        if not asset.is_active:
            return {"success": False, "reason": "Asset already removed"}
        asset.is_active = False
        wl = session.query(Watchlist).filter(
            Watchlist.symbol == symbol.upper(),
        ).first()
        if wl:
            wl.is_active = False
        session.commit()
        return {"success": True, "reason": f"{symbol.upper()} removed from universe"}