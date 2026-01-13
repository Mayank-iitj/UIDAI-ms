"""
Data Validation Utilities for UIDAI Intelligence System
Schema validation, constraint checking, and quality assurance
"""

import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UidaiDataValidator:
    """Validate UIDAI enrollment data against schema specifications"""
    
    def __init__(self, schema_path: str = "./config/schema.yaml"):
        """Initialize validator with schema configuration"""
        with open(schema_path, 'r') as f:
            self.schema = yaml.safe_load(f)
        
        self.columns_schema = self.schema['columns']
        self.quality_rules = self.schema['quality_rules']
        self.expected_ranges = self.schema['expected_ranges']
        
        logger.info("Initialized UidaiDataValidator")
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame against expected schema
        
        Args:
            df: Input DataFrame
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required columns
        expected_cols = set(self.columns_schema.keys())
        actual_cols = set(df.columns)
        
        missing_cols = expected_cols - actual_cols
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check data types and constraints
        for col_name, col_spec in self.columns_schema.items():
            if col_name not in df.columns:
                continue
            
            # Check nullable constraint
            if not col_spec.get('nullable', True):
                null_count = df[col_name].isna().sum()
                if null_count > 0:
                    errors.append(
                        f"Column '{col_name}' has {null_count} null values "
                        f"but is marked as non-nullable"
                    )
            
            # Check numeric constraints
            if 'constraints' in col_spec and col_name in df.columns:
                constraints = col_spec['constraints']
                
                if 'min' in constraints:
                    min_val = constraints['min']
                    violating = df[df[col_name] < min_val]
                    if len(violating) > 0:
                        errors.append(
                            f"Column '{col_name}' has {len(violating)} values "
                            f"below minimum {min_val}"
                        )
                
                if 'max' in constraints:
                    max_val = constraints['max']
                    violating = df[df[col_name] > max_val]
                    if len(violating) > 0:
                        errors.append(
                            f"Column '{col_name}' has {len(violating)} values "
                            f"above maximum {max_val}"
                        )
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("✓ Schema validation passed")
        else:
            logger.warning(f"✗ Schema validation failed with {len(errors)} errors")
        
        return is_valid, errors
    
    def check_quality_rules(self, df: pd.DataFrame) -> Dict[str, dict]:
        """
        Check all data quality rules
        
        Args:
            df: Input DataFrame
        
        Returns:
            Dictionary of rule results
        """
        results = {}
        
        # Rule 1: No negative enrollments
        negative_check = {
            'rule': 'no_negative_enrollments',
            'description': self.quality_rules['no_negative_enrollments']['description'],
            'passed': True,
            'violations': []
        }
        
        for col in ['age_0_5', 'age_5_17', 'age_18_plus']:
            negative_values = df[df[col] < 0]
            if len(negative_values) > 0:
                negative_check['passed'] = False
                negative_check['violations'].append({
                    'column': col,
                    'count': len(negative_values),
                    'sample_indices': negative_values.index[:5].tolist()
                })
        
        results['no_negative_enrollments'] = negative_check
        
        # Rule 2: Total equals sum
        total_check = {
            'rule': 'total_equals_sum',
            'description': self.quality_rules['total_equals_sum']['description'],
            'passed': True,
            'violations': []
        }
        
        if 'total_enrollment' in df.columns:
            calculated_total = df['age_0_5'] + df['age_5_17'] + df['age_18_plus']
            mismatch = df[df['total_enrollment'] != calculated_total]
            
            if len(mismatch) > 0:
                total_check['passed'] = False
                total_check['violations'].append({
                    'count': len(mismatch),
                    'sample_indices': mismatch.index[:5].tolist()
                })
        
        results['total_equals_sum'] = total_check
        
        # Rule 3: No duplicates
        duplicate_check = {
            'rule': 'no_duplicates',
            'description': self.quality_rules['no_duplicates']['description'],
            'passed': True,
            'violations': []
        }
        
        unique_keys = self.quality_rules['no_duplicates']['unique_keys']
        duplicates = df[df.duplicated(subset=unique_keys, keep=False)]
        
        if len(duplicates) > 0:
            duplicate_check['passed'] = False
            duplicate_check['violations'].append({
                'count': len(duplicates),
                'duplicate_groups': duplicates.groupby(unique_keys).size().head(5).to_dict()
            })
        
        results['no_duplicates'] = duplicate_check
        
        # Summary
        total_rules = len(results)
        passed_rules = sum(1 for r in results.values() if r['passed'])
        
        logger.info(f"Quality rules check: {passed_rules}/{total_rules} passed")
        
        return results
    
    def validate_states(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that all state names are in the reference list
        
        Args:
            df: Input DataFrame
        
        Returns:
            (is_valid, list_of_invalid_states)
        """
        if 'reference' not in self.schema or 'valid_states' not in self.schema['reference']:
            logger.warning("No reference state list found in schema")
            return True, []
        
        valid_states = set(self.schema['reference']['valid_states'])
        actual_states = set(df['state'].unique())
        
        invalid_states = actual_states - valid_states
        
        if invalid_states:
            logger.warning(f"Found {len(invalid_states)} invalid state names: {invalid_states}")
            return False, list(invalid_states)
        else:
            logger.info(f"✓ All {len(actual_states)} states are valid")
            return True, []
    
    def get_validation_report(self, df: pd.DataFrame) -> dict:
        """
        Run all validations and return comprehensive report
        
        Args:
            df: Input DataFrame
        
        Returns:
            Validation report dictionary
        """
        logger.info("Running comprehensive validation...")
        
        # Schema validation
        schema_valid, schema_errors = self.validate_schema(df)
        
        # Quality rules
        quality_results = self.check_quality_rules(df)
        
        # State validation
        states_valid, invalid_states = self.validate_states(df)
        
        report = {
            'timestamp': pd.Timestamp.now(),
            'total_records': len(df),
            'schema_validation': {
                'passed': schema_valid,
                'errors': schema_errors
            },
            'quality_rules': quality_results,
            'state_validation': {
                'passed': states_valid,
                'invalid_states': invalid_states
            },
            'overall_status': schema_valid and states_valid and all(
                rule['passed'] for rule in quality_results.values()
            )
        }
        
        if report['overall_status']:
            logger.info("✅ All validations passed!")
        else:
            logger.warning("⚠️ Some validations failed. Review the report.")
        
        return report


def main():
    """Test the validator"""
    from data_loader import UidaiDataLoader
    
    # Load data
    loader = UidaiDataLoader()
    df = loader.load_all_data()
    
    # Validate
    validator = UidaiDataValidator()
    report = validator.get_validation_report(df)
    
    print("\n=== Validation Report ===")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Records: {report['total_records']:,}")
    print(f"\nOverall Status: {'✅ PASSED' if report['overall_status'] else '⚠️ FAILED'}")
    
    print("\n--- Schema Validation ---")
    print(f"Passed: {report['schema_validation']['passed']}")
    if report['schema_validation']['errors']:
        print("Errors:")
        for error in report['schema_validation']['errors']:
            print(f"  - {error}")
    
    print("\n--- Quality Rules ---")
    for rule_name, rule_result in report['quality_rules'].items():
        status = "✓" if rule_result['passed'] else "✗"
        print(f"{status} {rule_name}: {rule_result['description']}")
        if not rule_result['passed'] and rule_result['violations']:
            for violation in rule_result['violations']:
                print(f"    Violations: {violation}")
    
    print("\n--- State Validation ---")
    print(f"Passed: {report['state_validation']['passed']}")
    if report['state_validation']['invalid_states']:
        print(f"Invalid States: {report['state_validation']['invalid_states']}")


if __name__ == "__main__":
    main()
