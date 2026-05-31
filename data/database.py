from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import event
from sqlalchemy.engine import Engine
from datetime import datetime
from utils.logger import system_logger, error_logger
from utils.config import config
import os

Base = declarative_base()

class MarketData(Base):
    __tablename__ = 'market_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    tick_volume = Column(Integer)

class Trade(Base):
    __tablename__ = 'trades'
    ticket = Column(Integer, primary_key=True)
    type = Column(String)  # 'BUY' or 'SELL'
    open_time = Column(DateTime)
    close_time = Column(DateTime, nullable=True)
    open_price = Column(Float)
    close_price = Column(Float, nullable=True)
    sl = Column(Float)
    tp = Column(Float)
    volume = Column(Float)
    profit = Column(Float, nullable=True)
    level = Column(Integer) # Martingale level 1, 2, or 3
    status = Column(String, default="OPEN") # OPEN, CLOSED

class TradeEvent(Base):
    __tablename__ = 'trade_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String) # OPEN, CLOSE, MODIFY, ERROR
    timestamp = Column(DateTime, default=datetime.utcnow)
    ticket = Column(Integer, nullable=True)
    message = Column(String)

class AccountSnapshot(Base):
    __tablename__ = 'account_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    balance = Column(Float)
    equity = Column(Float)
    margin = Column(Float)
    free_margin = Column(Float)

class BotState(Base):
    __tablename__ = 'bot_state'
    key = Column(String, primary_key=True)
    value = Column(JSON) # Store anything as JSON

class PerformanceMetrics(Base):
    __tablename__ = 'performance_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    win_rate = Column(Float)
    loss_rate = Column(Float)
    longest_win_streak = Column(Integer)
    longest_loss_streak = Column(Integer)
    level_2_activations = Column(Integer)
    level_3_activations = Column(Integer)
    total_trades = Column(Integer)
    daily_pnl = Column(Float)
    weekly_pnl = Column(Float)
    monthly_pnl = Column(Float)

class BacktestResult(Base):
    __tablename__ = 'backtest_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String)
    strategy = Column(String)
    duration_mode = Column(String)
    duration_val = Column(Integer)
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_profit = Column(Float)
    total_trades = Column(Integer)
    win_rate = Column(Float)
    account_blowups = Column(Integer)
    is_optimized = Column(Boolean, default=False)
    raw_config = Column(JSON, nullable=True)

class Database:
    def __init__(self):
        db_path = config.get('database', {}).get('db_path', 'trading_bot.sqlite')
        # Absolute path based on current working directory
        db_path = os.path.abspath(db_path)
        self.engine = create_engine(
            f'sqlite:///{db_path}', 
            echo=False,
            connect_args={'check_same_thread': False, 'timeout': 15}
        )
        self.Session = sessionmaker(bind=self.engine)
        self.init_db()

    def init_db(self):
        try:
            Base.metadata.create_all(self.engine)
            system_logger.info("Database initialized successfully.")
        except Exception as e:
            error_logger.error(f"Failed to initialize database: {e}")
            raise

    def get_session(self):
        return self.Session()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection).__name__ == 'Connection':
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

# Global database instance
db = Database()
