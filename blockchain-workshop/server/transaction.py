from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Transaction:
    source: str
    recipient: str
    amount: float
    timestamp: float = None
    is_valid: bool = True
    validation_error: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().timestamp()
            
    def to_dict(self) -> dict:
        """Convert transaction to a dictionary for JSON serialization"""
        return {
            'source': self.source,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'is_valid': self.is_valid,
            'validation_error': self.validation_error
        }
