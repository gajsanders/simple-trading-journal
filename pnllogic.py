import os
import io
import datetime as dt
from typing import Dict, Any, Tuple

import pandas as pd
import streamlit as st

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "trades.csv")

DEFAULT_COLUMNS = [
    "date", "symbol", "strategy",
    "entry_price", "exit_price", "quantity",
    "pnl", "notes", "status",
    # Extended fields for options
    "instrument_type",    # "Stock" or "Option"
    "option_type",        # "Call" or "Put"
    "strike",             # float
    "expiration",         # YYYY-MM-DD
    "contract_multiplier" # typically 100 for equity options
]

STRATEGIES = [
    "Long Stock", "Short Stock",
    "Long Call", "Short Call",
    "Long Put", "Short Put",
    "Covered Call", "Cash Secured Put",
    "Other",
]

# ---------- Data I/O ----------

def ensure_data_file() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        # Create empty CSV with default headers
        empty = pd.DataFrame(columns=DEFAULT_COLUMNS)
        empty.to_csv(DATA_FILE, index=False)

def load_trades() -> pd.DataFrame:
    ensure_data_file()
    df = pd.read_csv(DATA_FILE)
    # Ensure all default columns exist
    for col in DEFAULT_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    # Enforce dtypes and defaults
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["entry_price"] = pd.to_numeric(df["entry_price"], errors="coerce")
    df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df["strike"] = pd.to_numeric(df["strike"], errors="coerce")
    df["contract_multiplier"] = pd.to_numeric(df["contract_multiplier"], errors="coerce")

    # Fill logical defaults
    df["status"] = df["status"].fillna("Open")
    df["instrument_type"] = df["instrument_type"].fillna(df["strategy"].apply(_infer_instrument_from_strategy))
    df["contract_multiplier"] = df["contract_multiplier"].fillna(df["instrument_type"].apply(lambda x: 100 if x == "Option" else 1))
    # Normalize quantity sign conventions: store positive contracts/shares; capture direction via strategy
    # If legacy data stored negative for shorts, keep as-is in file but compute P&L using abs(quantity).
    return df

def save_trades(df: pd.DataFrame) -> None:
    # Ensure consistent column order
    for col in DEFAULT_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[DEFAULT_COLUMNS]
    df.to_csv(DATA_FILE, index=False)

# ---------- Helpers ----------

def _infer_instrument_from_strategy(strategy: str) -> str:
    if isinstance(strategy, str) and ("Call" in strategy or "Put" in strategy):
        return "Option"
    if strategy in ("Covered Call", "Cash Secured Put"):
        return "Option"
    return "Stock"

def _infer_option_type(strategy: str) -> str | None:
    if "Call" in str(strategy):
        return "Call"
    if "Put" in str(strategy):
        return "Put"
    return None

def _direction_from_strategy(strategy: str) -> int:
    """
    +1 for long exposure, -1 for short exposure.
    For options, 'Short Call/Put' and 'Cash Secured Put' are short (-1).
    Covered Call contains a short call leg; but here, treat it as short call leg for P&L entry/exit fields.
    """
    s = str(strategy)
    if s in ("Long Stock", "Long Call", "Long Put"):
        return +1
    if s in ("Short Stock", "Short Call", "Short Put", "Cash Secured Put"):
        return -1
    if s == "Covered Call":
        # For this simple journal, assume the recorded row corresponds to the short call leg
        return -1
    return +1

def _is_option(strategy: str) -> bool:
    return _infer_instrument_from_strategy(strategy) == "Option"

def _multiplier(row: pd.Series) -> float:
    # Use provided contract_multiplier, else default by instrument
    cm = row.get("contract_multiplier", None)
    if pd.isna(cm):
        return 100.0 if _is_option(row.get("strategy", "")) else 1.0
    return float(cm)

# ---------- P&L Logic ----------

def calculate_pnl_row(row: pd.Series) -> float:
    """
    Strategy-aware P&L calculation using row fields:
    - entry_price: price paid/received at entry (credit is positive for short options; use as absolute)
    - exit_price: price paid/received at exit (debit for BTC is positive absolute)
    - quantity: number of shares or contracts (use absolute magnitude)
    - strategy, instrument_type, option_type, strike, expiration, contract_multiplier
    - status: Open or Closed
    Notes:
    - For options, P&L uses multiplier (default 100).
    - For short options (Short Put/Call, Cash Secured Put), running P&L for a closed trade is (entry_credit - exit_debit)*multiplier*contracts.
    - For open option positions at expiration without exit, if fields allow (strike & underlying settlement S_T provided via exit_price as intrinsic?), compute intrinsic payoff path. This journal treats an “expiration without close” as: exit_price = intrinsic value at expiration (0 if OTM).
    """
    strategy = row.get("strategy", "")
    entry = _to_float(row.get("entry_price"))
    exitp = _to_float(row.get("exit_price"))
    qty = abs(_to_float(row.get("quantity")))
    direction = _direction_from_strategy(strategy)
    mult = _multiplier(row)
    instrument = row.get("instrument_type", _infer_instrument_from_strategy(strategy))
    opt_type = row.get("option_type", _infer_option_type(strategy))
    status = str(row.get("status", "Open"))

    # Guard
    if pd.isna(qty) or qty == 0 or pd.isna(entry):
        return 0.0

    # Stock logic
    if instrument == "Stock" and opt_type is None:
        # Long/Short Stock: P&L = (exit − entry) × shares for long; reverse sign for short via direction
        if pd.isna(exitp):
            return 0.0
        return float(direction) * (exitp - entry) * qty

    # Option logic
    # Default option P&L templates:
    # Long Call/Put: (exit - entry) * mult * qty
    # Short Call/Put: (entry - exit) * mult * qty
    # Cash Secured Put: same as Short Put for closed trades; expiration intrinsic if no exit
    if instrument == "Option":
        # If not specified, infer option type from strategy text
        if opt_type is None and isinstance(strategy, str):
            opt_type = _infer_option_type(strategy)
        # Running closed trade:
        if not pd.isna(exitp):
            # direction +1 => long option, -1 => short option
            # Use generic: pnl = direction * (exit - entry) * mult * qty
            return float(direction) * (exitp - entry) * mult * qty

        # Open trade without exit:
        # If still open and not expired, unrealized P&L is not computed (keep as 0 for simplicity).
        # If status is Closed but exit_price missing, try intrinsic-at-expiration path for short puts/cash-secured puts.
        if status == "Closed" and opt_type == "Put" and direction == -1:
            # Expect intrinsic value provided or computable; in minimal journal, use exit_price if provided;
            # otherwise assume expired OTM as 0 intrinsic for a closed-without-exit record.
            intrinsic = 0.0  # assume OTM if not provided
            return (entry - intrinsic) * mult * qty

        # Default: no P&L until exit
        return 0.0

    # Fallback
    if not pd.isna(exitp):
        return float(direction) * (exitp - entry) * qty
    return 0.0

def _to_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")

def recalc_pnl(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pnl"] = df.apply(calculate_pnl_row, axis=1)
    return df

# ---------- Metrics ----------

def calculate_metrics(trades_df: pd.DataFrame) -> Dict[str, Any]:
    df = trades_df.copy()
    pnl = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)
    total_pnl = float(pnl.sum())
    total_trades = len(df)
    wins = int((pnl > 0).sum())
    win_rate = float(wins / total_trades) if total_trades > 0 else 0.0
    avg_trade = float(pnl.mean()) if total_trades > 0 else 0.0
    return {
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "avg_trade": avg_trade,
    }

# ---------- UI ----------

st.set_page_config(page_title="Simple Trading Journal", layout="wide")
st.title("Simple Trading Journal")

trades = load_trades()

with st.expander("Add New Trade", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        date = st.date_input("Date", value=dt.date.today())
        symbol = st.text_input("Symbol")
        strategy = st.selectbox("Strategy", STRATEGIES, index=STRATEGIES.index("Cash Secured Put") if "Cash Secured Put" in STRATEGIES else 0)
    with col2:
        entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01, format="%.4f")
        exit_price = st.number_input("Exit Price (blank if open)", min_value=0.0, step=0.01, format="%.4f")
        quantity = st.number_input("Quantity (shares or contracts)", min_value=0.0, step=1.0, format="%.0f")
    with col3:
        status = st.selectbox("Status", ["Open", "Closed"], index=0)
        notes = st.text_input("Notes")

    # Option metadata
    st.markdown("Option details (optional; recommended for options):")
    oc1, oc2, oc3, oc4 = st.columns(4)
    with oc1:
        instrument_type = st.selectbox("Instrument Type", ["Auto", "Stock", "Option"], index=0)
    with oc2:
        option_type = st.selectbox("Option Type", ["Auto", "Call", "Put"], index=0)
    with oc3:
        strike = st.number_input("Strike (options)", min_value=0.0, step=0.01, format="%.2f")
    with oc4:
        expiration = st.text_input("Expiration YYYY-MM-DD (options)", value="")
    cm = st.number_input("Contract Multiplier", min_value=0, step=1, value=0, help="0 = auto (100 for options, 1 for stock)")

    if st.button("Add Trade"):
        new = pd.DataFrame([{
            "date": date,
            "symbol": symbol.strip().upper(),
            "strategy": strategy,
            "entry_price": entry_price if entry_price > 0 else pd.NA,
            "exit_price": exit_price if exit_price > 0 else pd.NA,
            "quantity": quantity if quantity > 0 else pd.NA,
            "pnl": pd.NA,
            "notes": notes,
            "status": status,
            "instrument_type": None if instrument_type == "Auto" else instrument_type,
            "option_type": None if option_type == "Auto" else option_type,
            "strike": strike if strike > 0 else pd.NA,
            "expiration": expiration if expiration else pd.NA,
            "contract_multiplier": None if cm == 0 else cm,
        }])
        # Append, recalc P&L, save
        merged = pd.concat([trades, new], ignore_index=True)
        merged = recalc_pnl(merged)
        save_trades(merged)
        st.success("Trade added.")
        st.experimental_rerun()

# Import CSV
with st.expander("Import CSV", expanded=False):
    up = st.file_uploader("Upload CSV to append or merge", type=["csv"])
    if up is not None:
        try:
            raw = pd.read_csv(up)
            # Map headers if needed; ensure required fields exist
            for col in DEFAULT_COLUMNS:
                if col not in raw.columns:
                    raw[col] = pd.NA
            raw["date"] = pd.to_datetime(raw["date"], errors="coerce").dt.date
            merged = pd.concat([trades, raw], ignore_index=True)
            merged = load_trades() if merged is None else merged
            merged = recalc_pnl(merged)
            save_trades(merged)
            st.success("Import complete and P&L recalculated.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# Filters
st.subheader("Filters")
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    date_from = st.date_input("From", value=None)
with fc2:
    date_to = st.date_input("To", value=None)
with fc3:
    sym_filter = st.text_input("Symbol filter (optional)").strip().upper()
with fc4:
    status_filter = st.selectbox("Status filter", ["All", "Open", "Closed"], index=0)

filtered = trades.copy()
if date_from:
    filtered = filtered[filtered["date"] >= date_from]
if date_to:
    filtered = filtered[filtered["date"] <= date_to]
if sym_filter:
    filtered = filtered[filtered["symbol"].str.upper() == sym_filter]
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]

# Recalculate P&L for display (ensures legacy rows recomputed with new logic)
filtered = recalc_pnl(filtered)

# Metrics
st.subheader("Quick Stats")
metrics = calculate_metrics(filtered)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total P&L", f"{metrics['total_pnl']:.2f}")
m2.metric("Win Rate", f"{metrics['win_rate']*100:.1f}%")
m3.metric("Avg Trade", f"{metrics['avg_trade']:.2f}")
m4.metric("Trades", f"{metrics['total_trades']}")

# Simple P&L over time chart
st.subheader("P&L Over Time")
plot_df = filtered.copy()
plot_df = plot_df.dropna(subset=["date"])
plot_df = plot_df.sort_values("date")
cum = plot_df.groupby("date")["pnl"].sum().cumsum().reset_index()
st.line_chart(cum.set_index("date"))

# Editable table
st.subheader("Trade History")
edit_df = filtered.copy()
st.caption("Tip: Edit fields and click 'Save Changes' to persist; P&L will be recalculated using the new strategy-aware logic.")
edited = st.data_editor(edit_df, num_rows="dynamic", use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    if st.button("Save Changes"):
        # Merge edits back into full dataset by index alignment on filtered set
        # Easiest approach: write edited filtered rows back by position
        base = trades.copy()
        # Align on matching rows (fallback: overwrite by symbol/date/entry)
        # For simplicity: rebuild from edited + leftover rows not in edited index set
        # Identify a composite key
        def key(df):
            return df["date"].astype(str) + "|" + df["symbol"].astype(str) + "|" + df["strategy"].astype(str) + "|" + df["entry_price"].astype(str)

        base["__k__"] = key(base)
        edited["__k__"] = key(edited)

        # Update matched rows
        updated = base.copy()
        upd_map = edited.set_index("__k__").to_dict(orient="index")
        updated = updated.drop(columns=[c for c in ["__k__"] if c in updated.columns])
        # Replace rows that match keys
        base_keys = set(base["__k__"].tolist())
        out_rows = []
        for _, r in base.iterrows():
            k = r["__k__"]
            if k in upd_map:
                newr = pd.Series(upd_map[k])
                out_rows.append(newr)
            else:
                out_rows.append(r.drop(labels="__k__"))
        outdf = pd.DataFrame(out_rows)
        outdf = recalc_pnl(outdf)
        save_trades(outdf)
        st.success("Changes saved.")
        st.experimental_rerun()
with c2:
    # Export
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered CSV", data=csv_bytes, file_name="trades_filtered.csv", mime="text/csv")

