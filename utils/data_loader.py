"""
Data Loader Utility for UIDAI Intelligence System
Loads and preprocesses Aadhaar enrollment data from multiple CSV files
"""

import pandas as pd
import polars as pl
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Union
import yaml
import logging
from functools import lru_cache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UidaiDataLoader:
    """Load and preprocess UIDAI enrollment data"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize data loader with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.raw_data_path = Path(self.config['data']['raw_data_path'])
        self.date_format = self.config['schema']['date_format']
        self.required_columns = self.config['schema']['required_columns']
        
        logger.info(f"Initialized UidaiDataLoader with data path: {self.raw_data_path}")
    
    def load_all_data(self, use_polars: bool = False) -> Union[pd.DataFrame, pl.DataFrame]:
        """
        Load all CSV files from the raw data directory
        
        Args:
            use_polars: Use Polars for faster loading (default: False, uses Pandas)
        
        Returns:
            Concatenated DataFrame with all enrollment data
        """
        csv_files = list(self.raw_data_path.glob("*.csv"))
        
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.raw_data_path}")
        
        logger.info(f"Found {len(csv_files)} CSV file(s) to load")
        
        if use_polars:
            return self._load_with_polars(csv_files)
        else:
            return self._load_with_pandas(csv_files)
    
    def _load_with_pandas(self, csv_files: List[Path]) -> pd.DataFrame:
        """Load data using Pandas"""
        dfs = []
        
        for file in csv_files:
            logger.info(f"Loading {file.name}...")
            df = pd.read_csv(file, dtype={
                'state': 'str',
                'district': 'str',
                'pincode': 'Int64',
                'age_0_5': 'Int64',
                'age_5_17': 'Int64',
                'age_18_greater': 'Int64'
            })
            dfs.append(df)
        
        # Concatenate all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Loaded {len(combined_df):,} total records")
        
        # Parse dates
        combined_df = self._parse_dates(combined_df)
        
        # Add derived columns
        combined_df = self._add_derived_columns(combined_df)
        
        return combined_df
    
    def _load_with_polars(self, csv_files: List[Path]) -> pl.DataFrame:
        """Load data using Polars (faster for large datasets)"""
        dfs = []
        
        for file in csv_files:
            logger.info(f"Loading {file.name}...")
            df = pl.read_csv(str(file))
            dfs.append(df)
        
        # Concatenate all dataframes
        combined_df = pl.concat(dfs)
        logger.info(f"Loaded {len(combined_df):,} total records")
        
        return combined_df
    
    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse date column to datetime"""
        df['date'] = pd.to_datetime(df['date'], format=self.date_format, errors='coerce')
        
        # Add temporal features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['year_month'] = df['date'].dt.to_period('M')
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
    
    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns for analysis"""
        # Total enrollment
        df['total_enrollment'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
        
        # Age group proportions
        df['pct_age_0_5'] = (df['age_0_5'] / df['total_enrollment'] * 100).round(2)
        df['pct_age_5_17'] = (df['age_5_17'] / df['total_enrollment'] * 100).round(2)
        df['pct_age_18_greater'] = (df['age_18_greater'] / df['total_enrollment'] * 100).round(2)
        
        # Handle division by zero
        df[['pct_age_0_5', 'pct_age_5_17', 'pct_age_18_greater']] = df[
            ['pct_age_0_5', 'pct_age_5_17', 'pct_age_18_greater']
        ].fillna(0)
        
        logger.info("Added derived columns: total_enrollment, age_group_percentages")
        
        return df
    
    @lru_cache(maxsize=1)
    def get_cached_data(self) -> pd.DataFrame:
        """Load data with caching for performance"""
        return self.load_all_data()
    
    def get_aggregated_data(
        self, 
        df: pd.DataFrame,
        group_by: List[str],
        agg_func: str = 'sum'
    ) -> pd.DataFrame:
        """
        Aggregate enrollment data by specified dimensions
        
        Args:
            df: Input DataFrame
            group_by: Columns to group by (e.g., ['state', 'year_month'])
            agg_func: Aggregation function ('sum', 'mean', 'count')
        
        Returns:
            Aggregated DataFrame
        """
        age_cols = ['age_0_5', 'age_5_17', 'age_18_plus', 'total_enrollment']
        
        if agg_func == 'sum':
            agg_df = df.groupby(group_by)[age_cols].sum().reset_index()
        elif agg_func == 'mean':
            agg_df = df.groupby(group_by)[age_cols].mean().reset_index()
        elif agg_func == 'count':
            agg_df = df.groupby(group_by).size().reset_index(name='record_count')
        else:
            raise ValueError(f"Unsupported aggregation function: {agg_func}")
        
        return agg_df
    
    def filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filter data by date range
        
        Args:
            df: Input DataFrame
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        if start_date:
            start = pd.to_datetime(start_date)
            filtered_df = filtered_df[filtered_df['date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            filtered_df = filtered_df[filtered_df['date'] <= end]
        
        logger.info(f"Filtered to {len(filtered_df):,} records")
        
        return filtered_df
    
    def get_summary_stats(self, df: pd.DataFrame) -> dict:
        """Get summary statistics of the dataset"""
        stats = {
            'total_records': len(df),
            'date_range': {
                'min': df['date'].min(),
                'max': df['date'].max(),
                'span_days': (df['date'].max() - df['date'].min()).days
            },
            'geographic_coverage': {
                'num_states': df['state'].nunique(),
                'num_districts': df['district'].nunique(),
                'num_pincodes': df['pincode'].nunique()
            },
            'enrollment_totals': {
                'age_0_5': int(df['age_0_5'].sum()),
                'age_5_17': int(df['age_5_17'].sum()),
                'age_18_greater': int(df['age_18_greater'].sum()),
                'total': int(df['total_enrollment'].sum())
            },
            'missing_data': {
                col: int(df[col].isna().sum()) for col in df.columns
            }
        }
        
        return stats


def main():
    """Test the data loader"""
    loader = UidaiDataLoader()
    
    # Load data
    df = loader.load_all_data()
    
    # Get summary
    stats = loader.get_summary_stats(df)
    
    print("\n=== UIDAI Dataset Summary ===")
    print(f"Total Records: {stats['total_records']:,}")
    print(f"\nDate Range: {stats['date_range']['min']} to {stats['date_range']['max']}")
    print(f"Span: {stats['date_range']['span_days']} days")
    print(f"\nGeographic Coverage:")
    print(f"  States: {stats['geographic_coverage']['num_states']}")
    print(f"  Districts: {stats['geographic_coverage']['num_districts']}")
    print(f"  PIN Codes: {stats['geographic_coverage']['num_pincodes']}")
    print(f"\nTotal Enrollments:")
    print(f"  Age 0-5: {stats['enrollment_totals']['age_0_5']:,}")
    print(f"  Age 5-17: {stats['enrollment_totals']['age_5_17']:,}")
    print(f"  Age 18+: {stats['enrollment_totals']['age_18_greater']:,}")
    print(f"  Total: {stats['enrollment_totals']['total']:,}")
    
    print("\n=== Sample Data ===")
    print(df.head())


if __name__ == "__main__":
    main()
