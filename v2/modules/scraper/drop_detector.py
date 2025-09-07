"""Enhanced drop detector with improved algorithms"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from bs4 import BeautifulSoup, Tag

from v2.core.exceptions import AnalysisError, CalculationError
from v2.core.utils import get_timestamp


class DropConfidence(Enum):
    """Drop detection confidence levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DropType(Enum):
    """Types of drops detected"""
    ODDS_DROP = "odds_drop"
    VOLUME_DROP = "volume_drop"
    PERCENTAGE_DROP = "percentage_drop"
    CSS_INDICATOR = "css_indicator"
    COMBINED = "combined"


@dataclass
class DropInfo:
    """Information about a detected drop"""
    table_type: str
    row_index: int
    column_name: str
    drop_type: DropType
    confidence: DropConfidence
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    percentage_change: Optional[float] = None
    css_classes: List[str] = None
    detected_at: datetime = None
    detection_method: str = "unknown"
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()
        if self.css_classes is None:
            self.css_classes = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "table_type": self.table_type,
            "row_index": self.row_index,
            "column_name": self.column_name,
            "drop_type": self.drop_type.value,
            "confidence": self.confidence.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "percentage_change": self.percentage_change,
            "css_classes": self.css_classes,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "detection_method": self.detection_method
        }


class EnhancedDropDetector:
    """Enhanced drop detector with multiple detection methods"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced drop detector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Detection thresholds (optimized based on analysis)
        self.thresholds = {
            "1x2": {
                "min_drop_percentage": 5.0,
                "significant_drop_percentage": 10.0,
                "major_drop_percentage": 20.0
            },
            "total": {
                "min_drop_percentage": 3.0,
                "significant_drop_percentage": 8.0,
                "major_drop_percentage": 15.0
            },
            "handicap": {
                "min_drop_percentage": 4.0,
                "significant_drop_percentage": 12.0,
                "major_drop_percentage": 25.0
            },
            "1x2_ht": {
                "min_drop_percentage": 6.0,
                "significant_drop_percentage": 15.0,
                "major_drop_percentage": 30.0
            }
        }
        
        # CSS classes that indicate drops
        self.drop_css_classes = {
            "red1": DropConfidence.LOW,
            "red2": DropConfidence.MEDIUM,
            "red3": DropConfidence.HIGH,
            "drop-indicator": DropConfidence.MEDIUM,
            "significant-drop": DropConfidence.HIGH,
            "major-drop": DropConfidence.VERY_HIGH
        }
        
        # Columns to monitor for drops
        self.monitored_columns = {
            "1x2": ["home_odd", "draw_odd", "away_odd"],
            "total": ["over", "under", "handicap"],
            "handicap": ["home_handicap", "away_handicap"],
            "1x2_ht": ["home_ht", "draw_ht", "away_ht"]
        }
        
        # Statistics
        self.stats = {
            "total_detections": 0,
            "css_detections": 0,
            "column_detections": 0,
            "hybrid_detections": 0,
            "confidence_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "very_high": 0
            },
            "last_detection": None
        }
    
    def detect_drops(self, soup: BeautifulSoup, table_type: str, 
                    previous_data: Optional[Dict] = None) -> List[DropInfo]:
        """Detect drops using hybrid approach
        
        Args:
            soup: BeautifulSoup object of the page
            table_type: Type of table (1x2, total, handicap, etc.)
            previous_data: Previous extraction data for comparison
            
        Returns:
            List of detected drops
        """
        drops = []
        
        try:
            self.logger.debug(f"Starting drop detection for table type: {table_type}")
            
            # Method 1: CSS-based detection
            css_drops = self._detect_drops_by_css(soup, table_type)
            drops.extend(css_drops)
            
            # Method 2: Column-based detection (primary method)
            if previous_data:
                column_drops = self._detect_drops_by_columns(soup, table_type, previous_data)
                drops.extend(column_drops)
            
            # Method 3: Hybrid validation
            validated_drops = self._validate_and_merge_drops(drops)
            
            # Update statistics
            self._update_stats(validated_drops)
            
            self.logger.info(f"Detected {len(validated_drops)} drops in {table_type} table")
            return validated_drops
            
        except Exception as e:
            self.logger.error(f"Drop detection failed for {table_type}: {e}")
            raise AnalysisError(f"Drop detection failed: {e}", "ANALYSIS_002")
    
    def _detect_drops_by_css(self, soup: BeautifulSoup, table_type: str) -> List[DropInfo]:
        """Detect drops using CSS classes
        
        Args:
            soup: BeautifulSoup object
            table_type: Table type
            
        Returns:
            List of detected drops
        """
        drops = []
        
        try:
            # Find all elements with drop-indicating CSS classes
            for css_class, confidence in self.drop_css_classes.items():
                elements = soup.find_all(class_=css_class)
                
                for element in elements:
                    # Try to determine the context (table row, column)
                    row_info = self._get_element_context(element)
                    
                    if row_info:
                        drop = DropInfo(
                            table_type=table_type,
                            row_index=row_info["row_index"],
                            column_name=row_info["column_name"],
                            drop_type=DropType.CSS_INDICATOR,
                            confidence=confidence,
                            css_classes=[css_class],
                            detection_method="css_classes"
                        )
                        drops.append(drop)
            
            self.stats["css_detections"] += len(drops)
            self.logger.debug(f"CSS detection found {len(drops)} drops")
            return drops
            
        except Exception as e:
            self.logger.warning(f"CSS-based detection failed: {e}")
            return []
    
    def _detect_drops_by_columns(self, soup: BeautifulSoup, table_type: str, 
                                previous_data: Dict) -> List[DropInfo]:
        """Detect drops by comparing column values
        
        Args:
            soup: BeautifulSoup object
            table_type: Table type
            previous_data: Previous data for comparison
            
        Returns:
            List of detected drops
        """
        drops = []
        
        try:
            # Get current data
            current_data = self._extract_table_data(soup, table_type)
            
            # Compare with previous data
            columns_to_check = self.monitored_columns.get(table_type, [])
            
            for row_index, current_row in current_data.items():
                if row_index not in previous_data:
                    continue
                
                previous_row = previous_data[row_index]
                
                for column in columns_to_check:
                    drop_info = self._compare_column_values(
                        table_type, row_index, column,
                        previous_row.get(column), current_row.get(column)
                    )
                    
                    if drop_info:
                        drops.append(drop_info)
            
            self.stats["column_detections"] += len(drops)
            self.logger.debug(f"Column detection found {len(drops)} drops")
            return drops
            
        except Exception as e:
            self.logger.warning(f"Column-based detection failed: {e}")
            return []
    
    def _compare_column_values(self, table_type: str, row_index: int, column: str,
                              old_value: Any, new_value: Any) -> Optional[DropInfo]:
        """Compare column values to detect drops
        
        Args:
            table_type: Table type
            row_index: Row index
            column: Column name
            old_value: Previous value
            new_value: Current value
            
        Returns:
            DropInfo if drop detected, None otherwise
        """
        try:
            # Convert values to float for comparison
            old_float = self._safe_float_conversion(old_value)
            new_float = self._safe_float_conversion(new_value)
            
            if old_float is None or new_float is None:
                return None
            
            # Calculate percentage change
            if old_float == 0:
                return None
            
            percentage_change = ((new_float - old_float) / old_float) * 100
            
            # Check if this constitutes a drop (negative change)
            if percentage_change >= 0:
                return None
            
            # Get thresholds for this table type
            thresholds = self.thresholds.get(table_type, self.thresholds["1x2"])
            
            # Determine confidence based on drop magnitude
            abs_change = abs(percentage_change)
            
            if abs_change >= thresholds["major_drop_percentage"]:
                confidence = DropConfidence.VERY_HIGH
            elif abs_change >= thresholds["significant_drop_percentage"]:
                confidence = DropConfidence.HIGH
            elif abs_change >= thresholds["min_drop_percentage"]:
                confidence = DropConfidence.MEDIUM
            else:
                return None  # Below minimum threshold
            
            return DropInfo(
                table_type=table_type,
                row_index=row_index,
                column_name=column,
                drop_type=DropType.ODDS_DROP,
                confidence=confidence,
                old_value=str(old_value),
                new_value=str(new_value),
                percentage_change=percentage_change,
                detection_method="column_comparison"
            )
            
        except Exception as e:
            self.logger.warning(f"Column comparison failed for {column}: {e}")
            return None
    
    def _validate_and_merge_drops(self, drops: List[DropInfo]) -> List[DropInfo]:
        """Validate and merge drops from different detection methods
        
        Args:
            drops: List of detected drops
            
        Returns:
            Validated and merged drops
        """
        # Group drops by position (table_type, row_index, column_name)
        grouped_drops = {}
        
        for drop in drops:
            key = (drop.table_type, drop.row_index, drop.column_name)
            
            if key not in grouped_drops:
                grouped_drops[key] = []
            grouped_drops[key].append(drop)
        
        # Merge drops at the same position
        merged_drops = []
        
        for position, position_drops in grouped_drops.items():
            if len(position_drops) == 1:
                merged_drops.append(position_drops[0])
            else:
                # Multiple detection methods found drop at same position
                merged_drop = self._merge_drop_info(position_drops)
                merged_drops.append(merged_drop)
                self.stats["hybrid_detections"] += 1
        
        return merged_drops
    
    def _merge_drop_info(self, drops: List[DropInfo]) -> DropInfo:
        """Merge multiple DropInfo objects at the same position
        
        Args:
            drops: List of DropInfo objects to merge
            
        Returns:
            Merged DropInfo object
        """
        # Use the drop with highest confidence as base
        confidence_order = [DropConfidence.VERY_HIGH, DropConfidence.HIGH, 
                          DropConfidence.MEDIUM, DropConfidence.LOW]
        
        base_drop = min(drops, key=lambda d: confidence_order.index(d.confidence))
        
        # Merge information
        merged_css_classes = []
        detection_methods = []
        
        for drop in drops:
            merged_css_classes.extend(drop.css_classes)
            detection_methods.append(drop.detection_method)
        
        # Create merged drop
        merged_drop = DropInfo(
            table_type=base_drop.table_type,
            row_index=base_drop.row_index,
            column_name=base_drop.column_name,
            drop_type=DropType.COMBINED,
            confidence=base_drop.confidence,
            old_value=base_drop.old_value,
            new_value=base_drop.new_value,
            percentage_change=base_drop.percentage_change,
            css_classes=list(set(merged_css_classes)),
            detection_method="+".join(set(detection_methods))
        )
        
        return merged_drop
    
    def _extract_table_data(self, soup: BeautifulSoup, table_type: str) -> Dict[int, Dict[str, str]]:
        """Extract table data for comparison
        
        Args:
            soup: BeautifulSoup object
            table_type: Table type
            
        Returns:
            Dictionary of row data
        """
        data = {}
        
        try:
            # Find tables (implementation would depend on actual HTML structure)
            tables = soup.find_all('table')
            
            for table in tables:
                # Identify table type (this would need to be implemented based on actual HTML)
                if self._is_table_type(table, table_type):
                    rows = table.find_all('tr')
                    
                    for row_index, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        
                        if len(cells) >= 3:  # Minimum cells for meaningful data
                            row_data = {}
                            
                            # Extract cell values (mapping would depend on table structure)
                            for col_index, cell in enumerate(cells):
                                column_name = self._get_column_name(table_type, col_index)
                                if column_name:
                                    row_data[column_name] = cell.get_text().strip()
                            
                            data[row_index] = row_data
            
            return data
            
        except Exception as e:
            self.logger.warning(f"Table data extraction failed: {e}")
            return {}
    
    def _is_table_type(self, table: Tag, table_type: str) -> bool:
        """Check if table matches the specified type
        
        Args:
            table: BeautifulSoup table element
            table_type: Expected table type
            
        Returns:
            True if table matches type
        """
        # This would need to be implemented based on actual HTML structure
        # For now, return True as placeholder
        return True
    
    def _get_column_name(self, table_type: str, col_index: int) -> Optional[str]:
        """Get column name based on table type and column index
        
        Args:
            table_type: Table type
            col_index: Column index
            
        Returns:
            Column name or None
        """
        column_mappings = {
            "1x2": {0: "time", 1: "home_odd", 2: "draw_odd", 3: "away_odd"},
            "total": {0: "time", 1: "over", 2: "handicap", 3: "under"},
            "handicap": {0: "time", 1: "home_handicap", 2: "away_handicap"}
        }
        
        return column_mappings.get(table_type, {}).get(col_index)
    
    def _get_element_context(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Get context information for an element
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Context information dictionary
        """
        try:
            # Find parent row
            row = element.find_parent('tr')
            if not row:
                return None
            
            # Find parent table
            table = element.find_parent('table')
            if not table:
                return None
            
            # Get row index
            rows = table.find_all('tr')
            row_index = rows.index(row) if row in rows else -1
            
            # Get column index
            cells = row.find_all(['td', 'th'])
            cell = element.find_parent(['td', 'th'])
            col_index = cells.index(cell) if cell and cell in cells else -1
            
            return {
                "row_index": row_index,
                "column_index": col_index,
                "column_name": f"col_{col_index}"
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get element context: {e}")
            return None
    
    def _safe_float_conversion(self, value: Any) -> Optional[float]:
        """Safely convert value to float
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None if conversion fails
        """
        if value is None:
            return None
        
        try:
            # Handle string values
            if isinstance(value, str):
                # Remove common non-numeric characters
                cleaned = value.replace(',', '').replace('%', '').strip()
                
                # Handle empty strings
                if not cleaned:
                    return None
                
                return float(cleaned)
            
            # Handle numeric values
            return float(value)
            
        except (ValueError, TypeError):
            return None
    
    def _update_stats(self, drops: List[DropInfo]) -> None:
        """Update detection statistics
        
        Args:
            drops: List of detected drops
        """
        self.stats["total_detections"] += len(drops)
        
        for drop in drops:
            self.stats["confidence_distribution"][drop.confidence.value] += 1
        
        if drops:
            self.stats["last_detection"] = datetime.now().isoformat()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset detection statistics"""
        self.stats = {
            "total_detections": 0,
            "css_detections": 0,
            "column_detections": 0,
            "hybrid_detections": 0,
            "confidence_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "very_high": 0
            },
            "last_detection": None
        }
        
        self.logger.info("Detection statistics reset")
    
    def configure_thresholds(self, table_type: str, thresholds: Dict[str, float]) -> None:
        """Configure detection thresholds for a table type
        
        Args:
            table_type: Table type to configure
            thresholds: Threshold configuration
        """
        if table_type not in self.thresholds:
            self.thresholds[table_type] = {}
        
        self.thresholds[table_type].update(thresholds)
        self.logger.info(f"Updated thresholds for {table_type}: {thresholds}")