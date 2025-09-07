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
            },
            "total_ht": {
                "min_drop_percentage": 3.0,
                "significant_drop_percentage": 8.0,
                "major_drop_percentage": 15.0
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
        
        # Columns to monitor for drops based on table type
        self.monitored_columns = {
            "1x2": ["home_percentage", "away_percentage"],  # Para 1x2: drops estão nas colunas home% e away%
            "total": ["drop"],  # Para total: drops estão na coluna drop
            "handicap": ["sharpness"],  # Para handicap: drops estão na coluna sharpness
            "1x2_ht": ["home_percentage", "away_percentage"],  # Para 1x2_ht: drops estão nas colunas home% e away%
            "total_ht": ["drop"]  # Para total_ht: drops estão na coluna drop
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
    
    def detect_drops(self, table_data: Dict, table_type: str) -> List[DropInfo]:
        """
        Detecta drops nas odds baseado nos thresholds configurados.
        
        Args:
            table_data: Dados da tabela extraídos
            table_type: Tipo da tabela (1x2, total, handicap, etc.)
            
        Returns:
            Lista de DropInfo com os drops detectados
        """
        drops = []
        
        if not table_data or 'data' not in table_data:
            return drops
            
        data_rows = table_data['data']
        if not data_rows:
            return drops
            
        # Usar detecção específica por colunas baseada no tipo de tabela
        drops.extend(self._detect_drops_by_specific_columns_test(data_rows, table_type))
        
        return drops
    
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
    
    def _detect_drops_by_specific_columns(self, soup: BeautifulSoup, table_type: str) -> List[DropInfo]:
        """Detect drops using specific columns for each table type
        
        Args:
            soup: BeautifulSoup object
            table_type: Table type
            
        Returns:
            List of detected drops
        """
        drops = []
        
        try:
            # Get current data
            current_data = self._extract_table_data(soup, table_type)
            
            # Check specific columns based on table type
            if table_type == "1x2":
                drops.extend(self._detect_1x2_drops(current_data))
            elif table_type == "total":
                drops.extend(self._detect_total_drops(current_data))
            elif table_type == "handicap":
                drops.extend(self._detect_handicap_drops(current_data))
            elif table_type == "1x2_ht":
                drops.extend(self._detect_1x2_ht_drops(current_data))
            elif table_type == "total_ht":
                drops.extend(self._detect_total_ht_drops(current_data))
            
            self.logger.debug(f"Specific column detection found {len(drops)} drops")
            return drops
            
        except Exception as e:
            self.logger.warning(f"Specific column detection failed: {e}")
            return []
    
    def _detect_1x2_drops(self, current_data: Dict) -> List[DropInfo]:
        """Detecta drops em tabelas 1x2 usando as colunas home% e away%"""
        drops = []
        
        for row_index, row_data in current_data.items():
            # Para 1x2: usa as colunas home% e away% diretamente
            home_percentage = self._parse_percentage(row_data.get('home_percentage', '0%'))
            away_percentage = self._parse_percentage(row_data.get('away_percentage', '0%'))
            
            # Verifica se os percentuais excedem os thresholds
            if abs(home_percentage) >= self.thresholds['1x2']['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="1x2",
                    row_index=row_index,
                    column_name="home_percentage",
                    drop_type=DropType.PERCENTAGE_DROP,
                    confidence=self._get_confidence_by_percentage(abs(home_percentage)),
                    new_value=f"{home_percentage}%",
                    percentage_change=home_percentage,
                    detection_method="specific_column_1x2"
                ))
                
            if abs(away_percentage) >= self.thresholds['1x2']['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="1x2",
                    row_index=row_index,
                    column_name="away_percentage",
                    drop_type=DropType.PERCENTAGE_DROP,
                    confidence=self._get_confidence_by_percentage(abs(away_percentage)),
                    new_value=f"{away_percentage}%",
                    percentage_change=away_percentage,
                    detection_method="specific_column_1x2"
                ))
                
        return drops
    
    def _detect_total_drops(self, current_data: Dict) -> List[DropInfo]:
        """Detecta drops em tabelas total usando a coluna drop"""
        drops = []
        
        for row_index, row_data in current_data.items():
            # Para total: usa a coluna drop diretamente
            drop_value = float(row_data.get('drop', 0) or 0)
            
            # Verifica se o drop excede o threshold
            if abs(drop_value) >= self.thresholds['total']['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="total",
                    row_index=row_index,
                    column_name="drop",
                    drop_type=DropType.VOLUME_DROP,
                    confidence=self._get_confidence_by_percentage(abs(drop_value)),
                    new_value=str(drop_value),
                    percentage_change=drop_value,
                    detection_method="specific_column_total"
                ))
                
        return drops
    
    def _detect_handicap_drops(self, current_data: Dict) -> List[DropInfo]:
        """Detecta drops em tabelas handicap usando a coluna sharpness"""
        drops = []
        
        for row_index, row_data in current_data.items():
            # Para handicap: usa a coluna sharpness diretamente
            sharpness_value = float(row_data.get('sharpness', 0) or 0)
            
            # Verifica se o sharpness excede o threshold
            if abs(sharpness_value) >= self.thresholds['handicap']['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="handicap",
                    row_index=row_index,
                    column_name="sharpness",
                    drop_type=DropType.ODDS_DROP,
                    confidence=self._get_confidence_by_percentage(abs(sharpness_value)),
                    new_value=str(sharpness_value),
                    percentage_change=sharpness_value,
                    detection_method="specific_column_handicap"
                ))
                
        return drops
    
    def _detect_1x2_ht_drops(self, current_data: Dict) -> List[DropInfo]:
        """Detecta drops em tabelas 1x2 half-time usando as colunas home% e away%"""
        drops = []
        
        for row_index, row_data in current_data.items():
            # Para 1x2_ht: usa as colunas home% e away% diretamente
            home_percentage = self._parse_percentage(row_data.get('home_percentage', '0%'))
            away_percentage = self._parse_percentage(row_data.get('away_percentage', '0%'))
            
            # Verifica se os percentuais excedem os thresholds
            if abs(home_percentage) >= self.thresholds['1x2_ht']['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="1x2_ht",
                    row_index=row_index,
                    column_name="home_percentage",
                    drop_type=DropType.PERCENTAGE_DROP,
                    confidence=self._get_confidence_by_percentage(abs(home_percentage)),
                    new_value=f"{home_percentage}%",
                    percentage_change=home_percentage,
                    detection_method="specific_column_1x2_ht"
                ))
                
            if abs(away_percentage) >= self.thresholds['1x2_ht']['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="1x2_ht",
                    row_index=row_index,
                    column_name="away_percentage",
                    drop_type=DropType.PERCENTAGE_DROP,
                    confidence=self._get_confidence_by_percentage(abs(away_percentage)),
                    new_value=f"{away_percentage}%",
                    percentage_change=away_percentage,
                    detection_method="specific_column_1x2_ht"
                ))
                
        return drops
    
    def _detect_total_ht_drops(self, current_data: Dict) -> List[DropInfo]:
        """Detecta drops em tabelas total half-time usando a coluna drop"""
        drops = []
        
        for row_index, row_data in current_data.items():
            # Para total_ht: usa a coluna drop diretamente
            drop_value = float(row_data.get('drop', 0) or 0)
            
            # Verifica se o drop excede o threshold
            if abs(drop_value) >= self.thresholds.get('total_ht', self.thresholds['total'])['min_drop_percentage']:
                drops.append(DropInfo(
                    table_type="total_ht",
                    row_index=row_index,
                    column_name="drop",
                    drop_type=DropType.VOLUME_DROP,
                    confidence=self._get_confidence_by_percentage(abs(drop_value)),
                    new_value=str(drop_value),
                    percentage_change=drop_value,
                    detection_method="specific_column_total_ht"
                ))
                
        return drops
    
    def _parse_percentage(self, value: str) -> float:
        """Parse percentage string to float
        
        Args:
            value: Percentage string (e.g., '5.2%', '-3.1%')
            
        Returns:
            Float value
        """
        try:
            if isinstance(value, str):
                # Remove % sign and convert to float
                cleaned = value.replace('%', '').strip()
                return float(cleaned) if cleaned else 0.0
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _get_confidence_by_percentage(self, percentage: float) -> DropConfidence:
        """Get confidence level based on percentage value
        
        Args:
            percentage: Absolute percentage value
            
        Returns:
            DropConfidence level
        """
        if percentage >= 20.0:
            return DropConfidence.VERY_HIGH
        elif percentage >= 10.0:
            return DropConfidence.HIGH
        elif percentage >= 5.0:
            return DropConfidence.MEDIUM
        else:
            return DropConfidence.LOW
    
    def _detect_drops_by_specific_columns_test(self, test_data: Dict, table_type: str) -> List[DropInfo]:
         """Test method for specific column detection
         
         Args:
             test_data: Test data dictionary
             table_type: Table type
             
         Returns:
             List of detected drops
         """
         drops = []
         
         try:
             # Check specific columns based on table type
             if table_type == "1x2":
                 drops.extend(self._detect_1x2_drops(test_data))
             elif table_type == "total":
                 drops.extend(self._detect_total_drops(test_data))
             elif table_type == "handicap":
                 drops.extend(self._detect_handicap_drops(test_data))
             elif table_type == "1x2_ht":
                 drops.extend(self._detect_1x2_ht_drops(test_data))
             elif table_type == "total_ht":
                 drops.extend(self._detect_total_ht_drops(test_data))
             
             return drops
             
         except Exception as e:
             self.logger.warning(f"Test detection failed: {e}")
             return []
     
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