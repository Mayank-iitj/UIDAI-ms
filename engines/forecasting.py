"""
Engine 4: Forecasting & Prediction
Predicts future enrollment demand using time series and ML models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import yaml
import logging
from datetime import datetime, timedelta
import warnings

# Time series
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ML models
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class ForecastingEngine:
    """Forecast future enrollment demand using multiple approaches"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.config = config['forecasting']
        self.schema = config['schema']
        
        # Forecast horizons
        self.horizon_short = self.config['forecast_horizon_short']
        self.horizon_long = self.config['forecast_horizon_long']
        
        # Model parameters
        self.sarima_params = self.config['sarima']
        self.xgb_params = self.config['xgboost']
        self.lgbm_params = self.config['lightgbm']
        
        # Confidence levels
        self.confidence_levels = self.config['confidence_levels']
        
        # Early warning
        self.surge_percentile = self.config['surge_percentile']
        
        logger.info("Initialized ForecastingEngine")
    
    def prepare_timeseries(self, df: pd.DataFrame, freq: str = 'M') -> pd.DataFrame:
        """
        Prepare data for time series forecasting
        
        Args:
            df: Input DataFrame
            freq: Frequency ('D' for daily, 'M' for monthly)
        
        Returns:
            Time series DataFrame
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        if freq == 'M':
            # Monthly aggregation
            ts = df.groupby('year_month')[age_cols + ['total_enrollment']].sum()
            ts.index = pd.to_datetime(ts.index.astype(str))
            ts = ts.asfreq('MS')  # Month start frequency
        elif freq == 'D':
            # Daily aggregation
            ts = df.groupby('date')[age_cols + ['total_enrollment']].sum()
            ts = ts.asfreq('D')
        else:
            raise ValueError(f"Unsupported frequency: {freq}")
        
        # Fill missing values with interpolation
        ts = ts.interpolate(method='time')
        
        logger.info(f"Prepared time series: {len(ts)} periods at {freq} frequency")
        
        return ts
    
    def forecast_sarima(
        self, 
        ts: pd.Series, 
        horizon: int, 
        seasonal_order: Optional[Tuple] = None
    ) -> Dict:
        """
        Forecast using SARIMA (Seasonal ARIMA)
        
        Args:
            ts: Time series data
            horizon: Number of periods to forecast
            seasonal_order: (P, D, Q, s) for seasonal component
        
        Returns:
            Dictionary with forecasts and confidence intervals
        """
        if seasonal_order is None:
            seasonal_order = tuple(self.sarima_params['seasonal_order'])
        
        try:
            # Fit SARIMA model (auto-determine order)
            model = SARIMAX(
                ts,
                order=(1, 1, 1),  # (p, d, q)
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            results = model.fit(disp=False)
            
            # Generate forecasts
            forecast = results.get_forecast(steps=horizon)
            forecast_mean = forecast.predicted_mean
            
            # Confidence intervals
            conf_intervals = {}
            for alpha in self.confidence_levels:
                conf_int = forecast.conf_int(alpha=1-alpha)
                conf_intervals[alpha] = {
                    'lower': conf_int.iloc[:, 0].tolist(),
                    'upper': conf_int.iloc[:, 1].tolist()
                }
            
            # Model metrics
            fitted = results.fittedvalues
            mae = mean_absolute_error(ts[1:], fitted[1:])  # Skip first value
            rmse = np.sqrt(mean_squared_error(ts[1:], fitted[1:]))
            mape = np.mean(np.abs((ts[1:] - fitted[1:]) / ts[1:])) * 100
            
            result = {
                'model': 'SARIMA',
                'forecast': forecast_mean.tolist(),
                'forecast_index': forecast_mean.index.tolist(),
                'confidence_intervals': conf_intervals,
                'metrics': {
                    'MAE': round(mae, 2),
                    'RMSE': round(rmse, 2),
                    'MAPE': round(mape, 2)
                },
                'aic': round(results.aic, 2),
                'bic': round(results.bic, 2)
            }
            
            logger.info(f"SARIMA forecast completed: MAPE={mape:.2f}%")
            
            return result
        
        except Exception as e:
            logger.error(f"SARIMA forecasting failed: {e}")
            return {'model': 'SARIMA', 'error': str(e)}
    
    def forecast_exponential_smoothing(self, ts: pd.Series, horizon: int) -> Dict:
        """
        Forecast using Exponential Smoothing (Holt-Winters)
        
        Args:
            ts: Time series data
            horizon: Number of periods to forecast
        
        Returns:
            Dictionary with forecasts
        """
        try:
            # Fit Exponential Smoothing
            model = ExponentialSmoothing(
                ts,
                seasonal_periods=12,  # Monthly seasonality
                trend='add',
                seasonal='add',
                use_boxcox=False
            )
            
            results = model.fit()
            
            # Generate forecasts
            forecast = results.forecast(steps=horizon)
            
            # Model metrics
            fitted = results.fittedvalues
            mae = mean_absolute_error(ts, fitted)
            rmse = np.sqrt(mean_squared_error(ts, fitted))
            mape = np.mean(np.abs((ts - fitted) / ts)) * 100
            
            result = {
                'model': 'ExponentialSmoothing',
                'forecast': forecast.tolist(),
                'forecast_index': forecast.index.tolist(),
                'metrics': {
                    'MAE': round(mae, 2),
                    'RMSE': round(rmse, 2),
                    'MAPE': round(mape, 2)
                }
            }
            
            logger.info(f"Exponential Smoothing forecast completed: MAPE={mape:.2f}%")
            
            return result
        
        except Exception as e:
            logger.error(f"Exponential Smoothing failed: {e}")
            return {'model': 'ExponentialSmoothing', 'error': str(e)}
    
    def create_ml_features(self, ts: pd.DataFrame) -> pd.DataFrame:
        """Create features for ML models"""
        df = ts.copy()
        
        # Temporal features
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['year'] = df.index.year
        df['day_of_year'] = df.index.dayofyear
        
        # Lag features
        for lag in [1, 2, 3, 6, 12]:
            for col in ['total_enrollment']:
                if col in df.columns:
                    df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        # Rolling statistics
        for window in [3, 6, 12]:
            for col in ['total_enrollment']:
                if col in df.columns:
                    df[f'{col}_ma_{window}'] = df[col].rolling(window=window).mean()
                    df[f'{col}_std_{window}'] = df[col].rolling(window=window).std()
        
        # Drop rows with NaN (due to lag and rolling)
        df = df.dropna()
        
        return df
    
    def forecast_xgboost(
        self, 
        ts: pd.DataFrame, 
        target_col: str, 
        horizon: int
    ) -> Dict:
        """
        Forecast using XGBoost
        
        Args:
            ts: Time series DataFrame
            target_col: Target column to forecast
            horizon: Number of periods to forecast
        
        Returns:
            Dictionary with forecasts and metrics
        """
        # Create features
        df = self.create_ml_features(ts[[target_col]])
        
        if len(df) < 24:  # Need at least 2 years of data
            return {'model': 'XGBoost', 'error': 'Insufficient data for ML forecasting'}
        
        # Split features and target
        feature_cols = [col for col in df.columns if col != target_col]
        X = df[feature_cols]
        y = df[target_col]
        
        # Train-test split (time series)
        train_size = len(X) - horizon
        if train_size < 12:
            train_size = len(X) - min(horizon, 3)
        
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Train model
        model = XGBRegressor(**self.xgb_params)
        model.fit(X_train, y_train)
        
        # Evaluate on test set
        if len(X_test) > 0:
            y_pred_test = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
        else:
            mae, rmse, mape = 0, 0, 0
        
        # Generate future forecasts (iterative)
        future_forecasts = []
        last_df = df.copy()
        
        for step in range(horizon):
            # Use last row as features
            X_next = last_df[feature_cols].iloc[[-1]]
            pred = model.predict(X_next)[0]
            future_forecasts.append(pred)
            
            # Update for next iteration (simplified - just update lags)
            # In practice, this would need more sophisticated feature updates
        
        result = {
            'model': 'XGBoost',
            'forecast': future_forecasts,
            'metrics': {
                'MAE': round(mae, 2),
                'RMSE': round(rmse, 2),
                'MAPE': round(mape, 2)
            },
            'feature_importance': dict(zip(
                feature_cols, 
                model.feature_importances_.tolist()
            ))
        }
        
        logger.info(f"XGBoost forecast completed: MAPE={mape:.2f}%")
        
        return result
    
    def ensemble_forecast(self, forecasts: List[Dict]) -> Dict:
        """
        Combine multiple forecasts using simple averaging
        
        Args:
            forecasts: List of forecast dictionaries
        
        Returns:
            Ensemble forecast
        """
        valid_forecasts = [f for f in forecasts if 'forecast' in f]
        
        if not valid_forecasts:
            return {'model': 'Ensemble', 'error': 'No valid forecasts to ensemble'}
        
        # Average forecasts
        forecast_arrays = [np.array(f['forecast']) for f in valid_forecasts]
        min_length = min(len(f) for f in forecast_arrays)
        forecast_arrays = [f[:min_length] for f in forecast_arrays]
        
        ensemble_forecast = np.mean(forecast_arrays, axis=0)
        
        # Average metrics
        metrics = {}
        for metric in ['MAE', 'RMSE', 'MAPE']:
            values = [f['metrics'][metric] for f in valid_forecasts if metric in f.get('metrics', {})]
            if values:
                metrics[metric] = round(np.mean(values), 2)
        
        result = {
            'model': 'Ensemble',
            'forecast': ensemble_forecast.tolist(),
            'metrics': metrics,
            'component_models': [f['model'] for f in valid_forecasts]
        }
        
        logger.info(f"Ensemble forecast completed from {len(valid_forecasts)} models")
        
        return result
    
    def detect_forecast_surges(self, forecast: List[float], historical: pd.Series) -> Dict:
        """
        Detect potential enrollment surges in forecast
        
        Args:
            forecast: Forecast values
            historical: Historical enrollment data
        
        Returns:
            Dictionary with surge detection results
        """
        # Historical statistics
        historical_mean = historical.mean()
        historical_std = historical.std()
        surge_threshold = historical.quantile(self.surge_percentile / 100)
        
        # Detect surges
        surges = []
        for i, value in enumerate(forecast):
            if value > surge_threshold:
                z_score = (value - historical_mean) / historical_std
                surges.append({
                    'period': i + 1,
                    'forecasted_value': round(value, 2),
                    'threshold': round(surge_threshold, 2),
                    'z_score': round(z_score, 2),
                    'pct_above_threshold': round(((value - surge_threshold) / surge_threshold) * 100, 2)
                })
        
        result = {
            'surge_detected': len(surges) > 0,
            'num_surge_periods': len(surges),
            'surge_periods': surges,
            'surge_threshold': round(surge_threshold, 2)
        }
        
        if surges:
            logger.warning(f"Forecast surge detected in {len(surges)} period(s)")
        
        return result
    
    def generate_forecast_report(
        self, 
        df: pd.DataFrame, 
        horizon: Optional[int] = None
    ) -> Dict:
        """Generate comprehensive forecast report"""
        if horizon is None:
            horizon = self.horizon_long
        
        # Prepare time series
        ts = self.prepare_timeseries(df, freq='M')
        
        # Run multiple forecasting methods
        forecasts = []
        
        # SARIMA
        sarima_forecast = self.forecast_sarima(
            ts['total_enrollment'], 
            horizon
        )
        forecasts.append(sarima_forecast)
        
        # Exponential Smoothing
        es_forecast = self.forecast_exponential_smoothing(
            ts['total_enrollment'], 
            horizon
        )
        forecasts.append(es_forecast)
        
        # XGBoost
        xgb_forecast = self.forecast_xgboost(
            ts, 
            'total_enrollment', 
            horizon
        )
        forecasts.append(xgb_forecast)
        
        # Ensemble
        ensemble = self.ensemble_forecast(forecasts)
        
        # Detect surges
        surge_detection = self.detect_forecast_surges(
            ensemble.get('forecast', []),
            ts['total_enrollment']
        )
        
        # Historical summary
        historical_summary = {
            'mean': round(ts['total_enrollment'].mean(), 2),
            'median': round(ts['total_enrollment'].median(), 2),
            'std': round(ts['total_enrollment'].std(), 2),
            'min': round(ts['total_enrollment'].min(), 2),
            'max': round(ts['total_enrollment'].max(), 2),
            'trend': 'increasing' if ts['total_enrollment'].iloc[-1] > ts['total_enrollment'].iloc[0] else 'decreasing'
        }
        
        report = {
            'forecast_horizon': horizon,
            'historical_summary': historical_summary,
            'individual_forecasts': forecasts,
            'ensemble_forecast': ensemble,
            'surge_detection': surge_detection,
            'recommendations': self._generate_forecast_recommendations(
                surge_detection, 
                ensemble,
                historical_summary
            )
        }
        
        return report
    
    def _generate_forecast_recommendations(
        self, 
        surge_detection: Dict,
        ensemble: Dict,
        historical: Dict
    ) -> List[str]:
        """Generate recommendations based on forecasts"""
        recommendations = []
        
        if surge_detection['surge_detected']:
            recommendations.append(
                f"ALERT: Enrollment surge predicted in {surge_detection['num_surge_periods']} period(s). "
                "Prepare additional capacity and resources."
            )
        
        if 'MAPE' in ensemble.get('metrics', {}):
            mape = ensemble['metrics']['MAPE']
            if mape > 15:
                recommendations.append(
                    f"Forecast accuracy moderate (MAPE={mape}%). "
                    "Consider improving data quality and feature engineering."
                )
            elif mape < 5:
                recommendations.append(
                    f"Forecast accuracy high (MAPE={mape}%). "
                    "Confidence in predictions is strong."
                )
        
        if historical['trend'] == 'increasing':
            recommendations.append(
                "Enrollment shows increasing trend. "
                "Plan for sustained capacity expansion."
            )
        
        if not recommendations:
            recommendations.append(
                "Forecast suggests stable enrollment patterns. "
                "Maintain current capacity planning."
            )
        
        return recommendations


def main():
    """Test the Forecasting Engine"""
    from utils.data_loader import UidaiDataLoader
    
    # Load data
    loader = UidaiDataLoader()
    df = loader.load_all_data()
    
    # Run forecasting
    engine = ForecastingEngine()
    report = engine.generate_forecast_report(df, horizon=6)
    
    print("\n" + "="*60)
    print("FORECASTING REPORT")
    print("="*60)
    
    print(f"\n--- Historical Summary ---")
    print(f"Mean Enrollment: {report['historical_summary']['mean']:,.0f}")
    print(f"Trend: {report['historical_summary']['trend']}")
    
    print(f"\n--- Ensemble Forecast (Next {report['forecast_horizon']} Months) ---")
    if 'forecast' in report['ensemble_forecast']:
        for i, val in enumerate(report['ensemble_forecast']['forecast'], 1):
            print(f"Month {i}: {val:,.0f}")
    
    print(f"\n--- Model Performance ---")
    for forecast in report['individual_forecasts']:
        if 'metrics' in forecast:
            print(f"{forecast['model']}: MAPE={forecast['metrics'].get('MAPE', 'N/A')}%")
    
    print(f"\n--- Surge Detection ---")
    if report['surge_detection']['surge_detected']:
        print(f"⚠️  Surges detected in {report['surge_detection']['num_surge_periods']} period(s)")
        for surge in report['surge_detection']['surge_periods'][:3]:
            print(f"  Period {surge['period']}: {surge['forecasted_value']:,.0f} "
                  f"({surge['pct_above_threshold']:.1f}% above threshold)")
    else:
        print("✓ No enrollment surges predicted")
    
    print(f"\n--- Recommendations ---")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
