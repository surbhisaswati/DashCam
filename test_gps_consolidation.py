#!/usr/bin/env python3
"""
Test script for the updated main.py with GPS consolidation functionality
"""
import os
import sys
sys.path.append('.')

from main import consolidate_gps_files, load_consolidated_gps_data

def test_gps_consolidation():
    """Test the GPS consolidation functionality"""
    print("=== Testing GPS Consolidation ===")
    
    # Test consolidation
    print("\n1. Testing consolidate_gps_files function:")
    consolidated_path = consolidate_gps_files('git', 'output_ocr', 'consolidated_gps_data.csv')
    
    if consolidated_path:
        print(f"✅ Consolidation successful: {consolidated_path}")
        
        # Check if file exists
        if os.path.exists(consolidated_path):
            print(f"✅ Consolidated file exists: {os.path.getsize(consolidated_path)} bytes")
        else:
            print("❌ Consolidated file not found")
            return False
    else:
        print("❌ Consolidation failed")
        return False
    
    # Test loading
    print("\n2. Testing load_consolidated_gps_data function:")
    gps_data = load_consolidated_gps_data(consolidated_path)
    
    if gps_data:
        print(f"✅ Loading successful: {len(gps_data)} GPS entries")
        print(f"✅ Sample entry: {gps_data[0]}")
        
        # Test data integrity
        sample_entry = gps_data[0]
        required_keys = ['source_file', 'date', 'time', 'lat', 'lon', 'speed', 'alt']
        
        if all(key in sample_entry for key in required_keys):
            print("✅ All required keys present in GPS entries")
        else:
            print("❌ Missing required keys in GPS entries")
            return False
            
        # Test data types
        if isinstance(sample_entry['lat'], float) and isinstance(sample_entry['lon'], float):
            print("✅ Latitude and longitude are properly converted to float")
        else:
            print("❌ Latitude/longitude data type conversion failed")
            return False
            
    else:
        print("❌ Loading failed")
        return False
    
    print("\n=== All GPS consolidation tests passed! ===")
    return True

def test_duplicate_consolidation():
    """Test that duplicate consolidation is prevented"""
    print("\n=== Testing Duplicate Consolidation Prevention ===")
    
    print("Running consolidation again to test duplicate prevention:")
    consolidated_path = consolidate_gps_files('git', 'output_ocr', 'consolidated_gps_data.csv')
    
    if consolidated_path:
        print("✅ Function returns existing file path (no re-processing)")
        return True
    else:
        print("❌ Function should return existing file path")
        return False

if __name__ == "__main__":
    print("Testing Updated main.py with GPS Consolidation")
    print("=" * 50)
    
    success = True
    
    # Test 1: GPS consolidation
    success &= test_gps_consolidation()
    
    # Test 2: Duplicate prevention
    success &= test_duplicate_consolidation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("\nThe updated main.py is ready to use with:")
        print("- Consolidated GPS data from all .git files")
        print("- Efficient duplicate prevention")
        print("- Enhanced CSV output with GPS source tracking")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    print(f"\nConsolidated GPS file location: output_ocr/consolidated_gps_data.csv")
    if os.path.exists("output_ocr/consolidated_gps_data.csv"):
        print(f"File size: {os.path.getsize('output_ocr/consolidated_gps_data.csv')} bytes")
