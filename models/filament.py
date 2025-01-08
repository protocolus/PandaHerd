from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class FilamentUsage(BaseModel):
    """Record of filament usage from a print job"""
    timestamp: datetime
    job_name: str
    grams_used: float
    purge_tower_grams: float = 0.0
    notes: Optional[str] = None

class SpoolWeight(BaseModel):
    """Manual weight measurement of a spool"""
    timestamp: datetime
    total_weight_g: float  # Total weight including spool
    notes: Optional[str] = None

class FilamentSpool(BaseModel):
    """Represents a filament spool in an AMS slot"""
    id: str
    name: str
    material: str  # PLA, PETG, etc.
    color: str  # Hex color code
    brand: str
    initial_weight_g: float = Field(default=1000.0)  # Usually 1kg
    empty_spool_weight_g: float = Field(default=250.0)  # Typical empty spool weight
    usage_history: List[FilamentUsage] = Field(default_factory=list)
    weight_measurements: List[SpoolWeight] = Field(default_factory=list)
    
    def get_remaining_weight(self) -> float:
        """Calculate remaining filament weight"""
        if self.weight_measurements:
            # Use the most recent manual weight measurement
            latest_weight = self.weight_measurements[-1].total_weight_g
            return max(0.0, latest_weight - self.empty_spool_weight_g)
        else:
            # Calculate based on usage history
            total_used = sum(usage.grams_used + usage.purge_tower_grams 
                           for usage in self.usage_history)
            return max(0.0, self.initial_weight_g - total_used)
    
    def get_remaining_percentage(self) -> float:
        """Calculate remaining filament percentage"""
        remaining = self.get_remaining_weight()
        return (remaining / self.initial_weight_g) * 100
    
    def record_usage(self, job_name: str, grams_used: float, 
                    purge_tower_grams: float = 0.0, notes: Optional[str] = None):
        """Record filament usage from a print job"""
        usage = FilamentUsage(
            timestamp=datetime.now(),
            job_name=job_name,
            grams_used=grams_used,
            purge_tower_grams=purge_tower_grams,
            notes=notes
        )
        self.usage_history.append(usage)
    
    def record_weight(self, total_weight_g: float, notes: Optional[str] = None):
        """Record a manual weight measurement"""
        if total_weight_g < self.empty_spool_weight_g:
            raise ValueError(
                f"Total weight ({total_weight_g}g) cannot be less than "
                f"empty spool weight ({self.empty_spool_weight_g}g)"
            )
        
        measurement = SpoolWeight(
            timestamp=datetime.now(),
            total_weight_g=total_weight_g,
            notes=notes
        )
        self.weight_measurements.append(measurement)
