# typedict - lets define a dictionary with fixed keys and specific types, like a form with labeled fields.
#optional - means a value can either be a specific type or none

from typing import TypedDict, Optional, Annotated
from datetime import datetime
from langgraph.graph import MessagesState

#1. Market Agent
#data structure for asset data: market agent fetches data and fill this details
class AssetData(TypedDict):
    symbol: str
    asset_type: str #crypto, stock
    price: float #current price
    volume_24h: float #how much traded in the last 34 hours in usd
    price_change_24h: float  #percentage change in price in the last 24 hours
    ohlcv: list[dict] #list od candles. each candle is a dicttionary like {"open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}

#2. Technical Agent
#Technical Agent fills after running chart analysis
class TechnicalSignal(TypedDict):
    symbol: str
    rsi: Optional[float]  #relative strength index. A number 0-100. Below 30 = oversold (possible BUY), above 70 = overbought (possible SELL)
    macd: Optional[float]  #Moving Average Convergence Divergence. A number. Positive = bullish, negative = bearish
    macd_signal: Optional[float] #the signal line that MACD is compared against
    bb_upper: Optional[float] #price touching upper band = possible sell
    bb_lower: Optional[float] #price touching lower band = possible buy
    signal: str    # final verdict from technical analysis: Buy, Sell, Hold
    signal_strength: float      # 0-100. How confident we are in the signal

#3. Sentiment Agent
#Sentiment Agent fills after sending headlines to GPT.
class SentimentResult(TypedDict):
    symbol: str
    sentiment: str    # GPT verdict on the news: Bullish, Bearish, Neutral
    confidence: float  # 0-100
    summary: str #A one sentence summary of why GPT thinks this way

#4. Risk Agent
#Risk Agent fills after running risk analysis
class RiskCheckResult(TypedDict):
    passed: bool #true - go head and send alert, false - block it
    reason: str #reason for passing or blocking

#5. Decision Agent
#Decision Agent fills - GPT takes technical + sentiment data and produces this.
class DecisionResult(TypedDict):
    symbol: str
    asset_type: str
    action: str    # final call:Buy, Sell, Hold
    confidence: int  # 0-100
    reasoning: str #reasoning behind the decision
    entry_zone: str   #recommended price zone to enter
    target: str #price target if the trade works out
    stop_loss: str #price to exit if market goes against you

#6. Alert Message - the formatted message ready to send
class AlertMessage(TypedDict):
    text: str  #the full formatted Telegram message with emojis and all details
    symbol: str
    action: str
    confidence: int

# class PipelineState(TypedDict):
    # run into
    # run_id: str
    # triggered_at: str
# 
    # Market data
    # all_assest_data: list[AssetData]
    # top_opportunities: list[str]
# 
    # Analysis
    # technical_signals: dict[str, TechnicalSignal]
    # sentiment_results: dict[str, SentimentResult]
# 
    # Risk + Decision
    # risk_check: Optional[RiskCheckResult]
    # decision: Optional[DecisionResult]
# 
    # Alert
    # alert_messages: Optional[AlertMessage]
    # alert_sent: bool
# 
    # Observability
    # errors: Annotated[list[str], operator.add]
    # token_usage: dict[str, int]
class PipelineState(dict):
    """
    Simple dict-based state that LangGraph passes fully between nodes.
    No TypedDict — avoids LangGraph's partial state merging issue.
    """
    pass

def initial_state(run_id: str) -> dict:
    return {
        "run_id":             run_id,
        "triggered_at":       datetime.utcnow().isoformat(),
        "all_asset_data":     [],
        "top_opportunities":  [],
        "technical_signals":  {},
        "sentiment_results":  {},
        "risk_check":         None,
        "decision":           None,
        "alert_message":      None,
        "alert_sent":         False,
        "errors":             [],
        "token_usage":        {},
    }
# def initial_state(run_id: str) -> PipelineState:
    # """Returns a clean state for every new pipeline run."""
    # return PipelineState(
        # run_id=run_id,
        # triggered_at=datetime.utcnow().isoformat(),
        # all_assest_data=[],  #list []
        # top_opportunities=[],
        # technical_signals={}, #dictionary {}
        # sentiment_results={},
        # risk_check=None,
        # decision=None,
        # alert_messages=None, #objects are none
        # alert_sent=False,
        # errors=[],
        # token_usage={},
    # )

