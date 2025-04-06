from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import re

class AuctionPreferences(BaseModel):
    """Auction preferences configuration."""
    default_buyers_premium: Decimal = Field(
        default=Decimal("0.15"),
        description="Default buyer's premium percentage",
        ge=Decimal("0"),
        le=Decimal("1")
    )
    sales_tax_rates: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Sales tax rates by state code"
    )
    preferred_auction_houses: List[str] = Field(
        default_factory=list,
        description="List of preferred auction houses"
    )

class EbayPreferences(BaseModel):
    """eBay account integration preferences."""
    api_credentials: Dict[str, str] = Field(
        default_factory=dict,
        description="eBay API credentials"
    )
    handling_time: int = Field(
        default=3,
        description="Default handling time in days",
        ge=1,
        le=30
    )
    return_policy: Dict[str, str] = Field(
        default_factory=lambda: {
            "type": "MoneyBack",
            "period": "Days_30",
            "shipping_paid_by": "Buyer"
        },
        description="Default return policy settings"
    )
    payment_methods: List[str] = Field(
        default_factory=lambda: ["PayPal", "CreditCard"],
        description="Accepted payment methods"
    )

class RiskProfile(BaseModel):
    """Risk profile configuration."""
    risk_level: Literal["Conservative", "Moderate", "Aggressive"] = Field(
        default="Moderate",
        description="Risk tolerance level"
    )
    max_return_rate: Decimal = Field(
        default=Decimal("0.15"),
        description="Maximum acceptable return rate",
        ge=Decimal("0"),
        le=Decimal("1")
    )
    blacklisted_categories: List[str] = Field(
        default_factory=list,
        description="Categories to avoid"
    )

class NotificationSettings(BaseModel):
    """Notification preferences."""
    email_alerts: Dict[str, bool] = Field(
        default_factory=lambda: {
            "new_auctions": True,
            "price_drops": True,
            "bid_confirmations": True
        },
        description="Email notification settings"
    )
    sms_alerts: Dict[str, bool] = Field(
        default_factory=lambda: {
            "new_auctions": False,
            "price_drops": False,
            "bid_confirmations": True
        },
        description="SMS notification settings"
    )
    email_address: Optional[str] = Field(
        default=None,
        description="Email address for notifications"
    )
    phone_number: Optional[str] = Field(
        default=None,
        description="Phone number for SMS notifications"
    )

class UserConfig(BaseModel):
    """Complete user configuration."""
    auction_preferences: AuctionPreferences = Field(
        default_factory=AuctionPreferences,
        description="Auction preferences"
    )
    ebay_preferences: EbayPreferences = Field(
        default_factory=EbayPreferences,
        description="eBay integration preferences"
    )
    risk_profile: RiskProfile = Field(
        default_factory=RiskProfile,
        description="Risk profile settings"
    )
    notification_settings: NotificationSettings = Field(
        default_factory=NotificationSettings,
        description="Notification preferences"
    )

    @validator("ebay_preferences")
    def validate_api_credentials(cls, v):
        """Validate eBay API credentials."""
        required_keys = ["app_id", "cert_id", "dev_id"]
        if not all(key in v.api_credentials for key in required_keys):
            raise ValueError("Missing required eBay API credentials")
        return v

    @validator("notification_settings")
    def validate_contact_info(cls, v):
        """Validate notification contact information."""
        if v.email_alerts["new_auctions"] and not v.email_address:
            raise ValueError("Email address required for email alerts")
        if v.sms_alerts["new_auctions"] and not v.phone_number:
            raise ValueError("Phone number required for SMS alerts")
        return v

class EbayConfig(BaseModel):
    """eBay API configuration."""
    app_id: str = Field(..., min_length=1, description="eBay application ID")
    cert_id: str = Field(..., min_length=1, description="eBay certificate ID")
    dev_id: str = Field(..., min_length=1, description="eBay developer ID")
    auth_token: str = Field(..., min_length=1, description="eBay OAuth token")

class AmazonConfig(BaseModel):
    """Amazon API configuration."""
    access_key: str = Field(..., min_length=1, description="Amazon access key")
    secret_key: str = Field(..., min_length=1, description="Amazon secret key")
    associate_tag: str = Field(..., min_length=1, description="Amazon associate tag")

class GoogleConfig(BaseModel):
    """Google API configuration."""
    api_key: str = Field(..., min_length=1, description="Google API key")

class ApiConfig(BaseModel):
    """API configuration section."""
    ebay: EbayConfig
    amazon: AmazonConfig
    google: GoogleConfig

class PreferencesConfig(BaseModel):
    """User preferences configuration."""
    output_format: str = Field(default="json", regex="^(json|yaml|csv)$", description="Output format for data")
    notifications: bool = Field(default=True, description="Enable notifications")
    auto_bid: bool = Field(default=False, description="Enable automatic bidding")
    max_bid_amount: float = Field(default=100.0, ge=0.0, description="Maximum bid amount")

    @validator("max_bid_amount")
    def validate_max_bid(cls, v):
        """Validate maximum bid amount."""
        if v <= 0:
            raise ValueError("Maximum bid amount must be greater than 0")
        return v

class DisplayConfig(BaseModel):
    """Display settings configuration."""
    dark_mode: bool = Field(default=False, description="Enable dark mode")
    currency: str = Field(default="USD", regex="^[A-Z]{3}$", description="Currency code")
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S", description="Date format string")

    @validator("currency")
    def validate_currency(cls, v):
        """Validate currency code."""
        if not re.match("^[A-Z]{3}$", v):
            raise ValueError("Currency must be a 3-letter code")
        return v

class HistoryConfig(BaseModel):
    """History settings configuration."""
    max_entries: int = Field(default=1000, ge=1, description="Maximum number of history entries")
    save_to_file: bool = Field(default=True, description="Save history to file")

    @validator("max_entries")
    def validate_max_entries(cls, v):
        """Validate maximum entries."""
        if v < 1:
            raise ValueError("Maximum entries must be at least 1")
        return v

class Config(BaseModel):
    """Main configuration schema."""
    version: str = Field(..., regex="^\\d+\\.\\d+\\.\\d+$", description="Configuration version")
    api: ApiConfig
    preferences: PreferencesConfig
    display: DisplayConfig
    history: HistoryConfig

    @validator("version")
    def validate_version(cls, v):
        """Validate version format."""
        if not re.match("^\\d+\\.\\d+\\.\\d+$", v):
            raise ValueError("Version must be in semantic versioning format (e.g., 1.0.0)")
        return v

def validate_config(config: Dict[str, Any]) -> Optional[str]:
    """Validate configuration against schema.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Error message if validation fails, None if successful
    """
    try:
        Config(**config)
        return None
    except Exception as e:
        return str(e)

def validate_api_keys(config: Dict[str, Any]) -> Dict[str, bool]:
    """Validate API keys format.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of API validation results
    """
    results = {
        "ebay": False,
        "amazon": False,
        "google": False
    }
    
    try:
        # Validate eBay API keys
        if "api" in config and "ebay" in config["api"]:
            ebay_config = config["api"]["ebay"]
            results["ebay"] = all([
                len(ebay_config.get("app_id", "")) > 0,
                len(ebay_config.get("cert_id", "")) > 0,
                len(ebay_config.get("dev_id", "")) > 0,
                len(ebay_config.get("auth_token", "")) > 0
            ])
        
        # Validate Amazon API keys
        if "api" in config and "amazon" in config["api"]:
            amazon_config = config["api"]["amazon"]
            results["amazon"] = all([
                len(amazon_config.get("access_key", "")) > 0,
                len(amazon_config.get("secret_key", "")) > 0,
                len(amazon_config.get("associate_tag", "")) > 0
            ])
        
        # Validate Google API key
        if "api" in config and "google" in config["api"]:
            google_config = config["api"]["google"]
            results["google"] = len(google_config.get("api_key", "")) > 0
        
        return results
    except Exception:
        return results

def validate_preferences(config: Dict[str, Any]) -> Dict[str, bool]:
    """Validate user preferences.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dictionary of preference validation results
    """
    results = {
        "output_format": False,
        "notifications": False,
        "auto_bid": False,
        "max_bid_amount": False
    }
    
    try:
        if "preferences" in config:
            prefs = config["preferences"]
            
            # Validate output format
            results["output_format"] = prefs.get("output_format") in ["json", "yaml", "csv"]
            
            # Validate notifications
            results["notifications"] = isinstance(prefs.get("notifications"), bool)
            
            # Validate auto bid
            results["auto_bid"] = isinstance(prefs.get("auto_bid"), bool)
            
            # Validate max bid amount
            max_bid = prefs.get("max_bid_amount")
            results["max_bid_amount"] = isinstance(max_bid, (int, float)) and max_bid > 0
        
        return results
    except Exception:
        return results

def validate_display_settings(config: Dict[str, Any]) -> Dict[str, bool]:
    """Validate display settings.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dictionary of display setting validation results
    """
    results = {
        "dark_mode": False,
        "currency": False,
        "date_format": False
    }
    
    try:
        if "display" in config:
            display = config["display"]
            
            # Validate dark mode
            results["dark_mode"] = isinstance(display.get("dark_mode"), bool)
            
            # Validate currency
            currency = display.get("currency", "")
            results["currency"] = bool(re.match("^[A-Z]{3}$", currency))
            
            # Validate date format
            date_format = display.get("date_format", "")
            results["date_format"] = bool(date_format)
        
        return results
    except Exception:
        return results

def validate_history_settings(config: Dict[str, Any]) -> Dict[str, bool]:
    """Validate history settings.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dictionary of history setting validation results
    """
    results = {
        "max_entries": False,
        "save_to_file": False
    }
    
    try:
        if "history" in config:
            history = config["history"]
            
            # Validate max entries
            max_entries = history.get("max_entries")
            results["max_entries"] = isinstance(max_entries, int) and max_entries > 0
            
            # Validate save to file
            results["save_to_file"] = isinstance(history.get("save_to_file"), bool)
        
        return results
    except Exception:
        return results 