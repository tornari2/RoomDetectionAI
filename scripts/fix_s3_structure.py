#!/usr/bin/env python3
"""
Fix S3 structure for training data.
Identifies and fixes path issues including double slashes, misplaced files, etc.
"""

import argparse
import boto3
from botocore.exceptions import ClientError
import sys

BUCKET_NAME = "room-detection-ai-blueprints-dev"
REGION = "us-east-2"

def list_s3_objects(prefix=''):
    """List all objects under a prefix."""
    s3_client = boto3.client('s3', region_name=REGION)
    objects = []
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
            if 'Contents' in page:
                objects.extend(page['Contents'])
    except ClientError as e:
        print(f"❌ Error listing objects: {e}")
        return []
    
    return objects

def analyze_structure():
    """Analyze S3 structure for path issues."""
    print("=" * 80)
    print("Analyzing S3 Structure")
    print("=" * 80)
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Region: {REGION}\n")
    
    # Get all training objects
    training_objects = list_s3_objects('training/')
    
    print(f"Total objects in training/: {len(training_objects)}\n")
    
    # Categorize objects
    issues = {
        'double_slash': [],
        'test_data': [],
        'outputs': [],
        'proper_training': [],
        'proper_validation': [],
    }
    
    for obj in training_objects:
        key = obj['Key']
        
        # Check for double slashes
        if '//' in key:
            issues['double_slash'].append(key)
        # Check for test data
        elif 'training/test/' in key:
            issues['test_data'].append(key)
        # Check for outputs
        elif 'training/outputs/' in key:
            issues['outputs'].append(key)
        # Check for proper training data
        elif key.startswith('training/images/') or key.startswith('training/labels/'):
            issues['proper_training'].append(key)
        # Check for proper validation data
        elif key.startswith('training/validation/images/') or key.startswith('training/validation/labels/'):
            issues['proper_validation'].append(key)
    
    # Print summary
    print("📊 Structure Analysis:")
    print(f"  ✓ Proper training data: {len(issues['proper_training'])} files")
    print(f"  ✓ Proper validation data: {len(issues['proper_validation'])} files")
    print(f"  ⚠️  Double slash paths: {len(issues['double_slash'])} files")
    print(f"  ⚠️  Test data (should move): {len(issues['test_data'])} files")
    print(f"  ℹ️  Output files: {len(issues['outputs'])} files")
    
    return issues

def fix_double_slashes(keys):
    """Fix double slash issues in S3 paths."""
    if not keys:
        print("\n✅ No double slash issues found")
        return
    
    print(f"\n🔧 Fixing {len(keys)} double slash paths...")
    print("   This may take a few minutes...")
    s3_client = boto3.client('s3', region_name=REGION)
    
    fixed_count = 0
    failed_count = 0
    
    for i, key in enumerate(keys, 1):
        # Replace double slashes with single slashes
        new_key = key.replace('//', '/')
        
        if key == new_key:
            continue
        
        try:
            # Copy to new location
            s3_client.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={'Bucket': BUCKET_NAME, 'Key': key},
                Key=new_key
            )
            
            # Delete old location
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
            
            fixed_count += 1
            # Show progress every 50 files
            if fixed_count % 50 == 0:
                percent = (i / len(keys)) * 100
                print(f"  Progress: {fixed_count}/{len(keys)} ({percent:.1f}%) files fixed...")
        except ClientError as e:
            print(f"  ❌ Failed to fix {key}: {e}")
            failed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} files")
    if failed_count > 0:
        print(f"❌ Failed {failed_count} files")

def move_test_data(keys):
    """Move test data out of training prefix to avoid conflicts."""
    if not keys:
        print("\n✅ No test data to move")
        return
    
    print(f"\n🔧 Moving {len(keys)} test files to separate location...")
    s3_client = boto3.client('s3', region_name=REGION)
    
    moved_count = 0
    failed_count = 0
    
    for key in keys:
        # Move from training/test/ to test/
        new_key = key.replace('training/test/', 'test/')
        
        try:
            # Copy to new location
            s3_client.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={'Bucket': BUCKET_NAME, 'Key': key},
                Key=new_key
            )
            
            # Delete old location
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
            
            moved_count += 1
            if moved_count % 100 == 0:
                print(f"  Moved {moved_count}/{len(keys)} files...")
        except ClientError as e:
            print(f"  ❌ Failed to move {key}: {e}")
            failed_count += 1
    
    print(f"✓ Moved {moved_count} files")
    if failed_count > 0:
        print(f"❌ Failed {failed_count} files")

def verify_structure():
    """Verify the fixed structure."""
    print("\n" + "=" * 80)
    print("Verifying Fixed Structure")
    print("=" * 80)
    
    training_objects = list_s3_objects('training/')
    
    # Check for remaining issues
    double_slash_count = sum(1 for obj in training_objects if '//' in obj['Key'])
    test_data_count = sum(1 for obj in training_objects if 'training/test/' in obj['Key'])
    
    training_images = sum(1 for obj in training_objects if obj['Key'].startswith('training/images/') and obj['Key'].endswith(('.png', '.jpg', '.jpeg')))
    training_labels = sum(1 for obj in training_objects if obj['Key'].startswith('training/labels/') and obj['Key'].endswith('.txt'))
    val_images = sum(1 for obj in training_objects if obj['Key'].startswith('training/validation/images/') and obj['Key'].endswith(('.png', '.jpg', '.jpeg')))
    val_labels = sum(1 for obj in training_objects if obj['Key'].startswith('training/validation/labels/') and obj['Key'].endswith('.txt'))
    
    print("\n📊 Final Structure:")
    print(f"  Training images: {training_images}")
    print(f"  Training labels: {training_labels}")
    print(f"  Validation images: {val_images}")
    print(f"  Validation labels: {val_labels}")
    print(f"\n  Remaining issues:")
    print(f"    Double slashes: {double_slash_count}")
    print(f"    Test data in training: {test_data_count}")
    
    if double_slash_count == 0 and test_data_count == 0:
        print("\n✅ Structure is clean!")
        return True
    else:
        print("\n⚠️  Some issues remain")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Fix S3 structure for training data')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, do not fix')
    args = parser.parse_args()
    
    print("\n")
    
    # Step 1: Analyze
    issues = analyze_structure()
    
    # Step 2: Ask for confirmation
    total_issues = len(issues['double_slash']) + len(issues['test_data'])
    
    if total_issues == 0:
        print("\n✅ No issues found! Structure is already clean.")
        return
    
    if args.analyze_only:
        print(f"\n📊 Analysis complete. Found {total_issues} issues (analyze-only mode, no fixes applied)")
        return
    
    print(f"\n⚠️  Found {total_issues} issues to fix")
    print("\nThis script will:")
    if issues['double_slash']:
        print(f"  1. Fix {len(issues['double_slash'])} double slash paths")
    if issues['test_data']:
        print(f"  2. Move {len(issues['test_data'])} test files to test/ (outside training/)")
    
    if not args.yes:
        response = input("\nProceed with fixes? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled")
            return
    else:
        print("\n✅ Auto-confirmed with --yes flag")
    
    # Step 3: Fix issues
    if issues['double_slash']:
        fix_double_slashes(issues['double_slash'])
    
    if issues['test_data']:
        move_test_data(issues['test_data'])
    
    # Step 4: Verify
    verify_structure()
    
    print("\n" + "=" * 80)
    print("Complete!")
    print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

