from sqlalchemy import Column, String, Integer, BigInteger, Date, ForeignKey, Index, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class Corporation(Base):
    """法人マスタ"""
    __tablename__ = "corporations"

    corporation_id = Column(String(13), primary_key=True, comment="法人番号")
    name = Column(String(200), nullable=False, comment="法人名称")
    type = Column(String(20), comment="法人種別（社会福祉法人/株式会社等）")
    postal_code = Column(String(7), comment="郵便番号")
    prefecture = Column(String(10), comment="都道府県")
    city = Column(String(50), comment="市区町村")
    address = Column(String(200), comment="詳細住所")
    established_date = Column(Date, comment="設立年月")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    facilities = relationship("Facility", back_populates="corporation", cascade="all, delete-orphan")
    financials = relationship("CorporationFinancial", back_populates="corporation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_corporation_prefecture", "prefecture"),
        Index("idx_corporation_type", "type"),
    )


class Facility(Base):
    """事業所マスタ"""
    __tablename__ = "facilities"

    facility_id = Column(String(20), primary_key=True, comment="事業所番号")
    corporation_id = Column(String(13), ForeignKey("corporations.corporation_id"), comment="法人番号")
    name = Column(String(200), nullable=False, comment="事業所名称")
    service_type = Column(String(50), comment="サービス種別（介護/障害/児童等）")
    service_detail = Column(String(100), comment="具体的サービス（訪問介護/デイサービス等）")
    capacity = Column(Integer, comment="定員")
    opened_date = Column(Date, comment="開設年月")
    postal_code = Column(String(7), comment="郵便番号")
    prefecture = Column(String(10), comment="都道府県")
    city = Column(String(50), comment="市区町村")
    address = Column(String(200), comment="詳細住所")
    management_type = Column(String(30), comment="経営主体種別（社会福祉法人/営利法人等）")
    match_status = Column(String(20), default="matched", comment="マッチング状態（matched/unmatched）")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    corporation = relationship("Corporation", back_populates="facilities")

    # Indexes
    __table_args__ = (
        Index("idx_facility_corporation", "corporation_id"),
        Index("idx_facility_prefecture", "prefecture"),
        Index("idx_facility_service_type", "service_type"),
    )


class CorporationFinancial(Base):
    """法人財務年次"""
    __tablename__ = "corporation_financials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    corporation_id = Column(String(13), ForeignKey("corporations.corporation_id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False, comment="対象年度（例：2022）")
    revenue = Column(BigInteger, comment="売上高（事業収益）")
    ordinary_profit = Column(BigInteger, comment="経常利益")
    net_assets = Column(BigInteger, comment="純資産額")
    total_assets = Column(BigInteger, comment="総資産額")
    employees = Column(Integer, comment="常勤換算職員数")
    report_url = Column(String(500), comment="報告書URL（原本PDF）")
    collected_at = Column(DateTime, default=datetime.utcnow, comment="データ収集日")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    corporation = relationship("Corporation", back_populates="financials")

    # Indexes
    __table_args__ = (
        Index("idx_financial_corporation_year", "corporation_id", "fiscal_year"),
        Index("idx_financial_corporation", "corporation_id"),
        Index("idx_financial_year", "fiscal_year"),
    )


class DataCollectionLog(Base):
    """データ収集実行ログ"""
    __tablename__ = "data_collection_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    script_name = Column(String(100), nullable=False, comment="スクリプト名（import_corporation_csv等）")
    status = Column(String(20), nullable=False, comment="ステータス（running/success/failed）")
    records_processed = Column(Integer, comment="処理件数")
    error_message = Column(Text, comment="エラーメッセージ")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="開始時刻")
    completed_at = Column(DateTime, comment="完了時刻")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_collection_logs_script", "script_name"),
        Index("idx_collection_logs_status", "status"),
        Index("idx_collection_logs_started", "started_at"),
    )


class ApiKey(Base):
    """API キー管理"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(256), nullable=False, unique=True, comment="ハッシング済みキー")
    name = Column(String(100), nullable=False, comment="キー名")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効/無効")
    expires_at = Column(DateTime, nullable=True, comment="有効期限")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True, comment="最後に使用した時刻")
    usage_count = Column(Integer, default=0, comment="使用回数")

    # Indexes
    __table_args__ = (
        Index("idx_api_keys_key_hash", "key_hash"),
        Index("idx_api_keys_is_active", "is_active"),
    )
