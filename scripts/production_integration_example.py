"""
Production Integration Example
===============================

Example showing how to integrate the OCR system into a larger
railway wagon inspection application.
"""

import os
import json
from datetime import datetime
from pathlib import Path


class WagonInspectionSystem:
    """
    Complete wagon inspection system integrating:
    - Temporal fusion for blur reduction
    - OCR for wagon number extraction
    - Database logging
    - Quality assurance
    """
    
    def __init__(self, fusion_weights='weights/gopro_best.pth', 
                 ocr_confidence=0.4, use_gpu=True):
        """
        Initialize inspection system.
        
        Args:
            fusion_weights: Path to deblurring model weights
            ocr_confidence: Minimum OCR confidence (0.0-1.0)
            use_gpu: Whether to use GPU acceleration
        """
        from temporal_fusion_wagon import TemporalFusionPipeline
        from run_ocr_wagon import WagonNumberOCR
        
        self.fusion_weights = fusion_weights
        self.ocr_confidence = ocr_confidence
        self.use_gpu = use_gpu
        
        # Initialize pipelines
        print("Initializing Wagon Inspection System...")
        self.fusion_pipeline = TemporalFusionPipeline(weights_path=fusion_weights)
        self.ocr_system = WagonNumberOCR(confidence_threshold=ocr_confidence)
        print("✓ System ready\n")
    
    def inspect_wagon(self, frame_paths, wagon_id=None, output_dir='inspections'):
        """
        Complete inspection of a wagon from multiple frames.
        
        Args:
            frame_paths: List of paths to consecutive frames
            wagon_id: Optional wagon identifier (for tracking)
            output_dir: Base directory for results
            
        Returns:
            dict: Inspection results with all metadata
        """
        # Create unique output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if wagon_id:
            inspection_dir = os.path.join(output_dir, f"{wagon_id}_{timestamp}")
        else:
            inspection_dir = os.path.join(output_dir, f"inspection_{timestamp}")
        
        os.makedirs(inspection_dir, exist_ok=True)
        
        # Initialize result structure
        result = {
            'inspection_id': f"{timestamp}_{wagon_id or 'unknown'}",
            'timestamp': timestamp,
            'wagon_id': wagon_id,
            'num_frames': len(frame_paths),
            'frames': [os.path.basename(p) for p in frame_paths],
            'output_dir': inspection_dir,
            'status': 'in_progress'
        }
        
        print("=" * 70)
        print("WAGON INSPECTION")
        print("=" * 70)
        print(f"Inspection ID: {result['inspection_id']}")
        print(f"Frames: {len(frame_paths)}")
        print(f"Output: {inspection_dir}/")
        print("=" * 70)
        print()
        
        try:
            # STAGE 1: Temporal Fusion
            print("STAGE 1: Temporal Fusion")
            print("-" * 70)
            
            self.fusion_pipeline.process_sequence(
                frame_paths,
                output_dir=inspection_dir,
                fusion_method='max_gradient'  # Best for text
            )
            
            result['fusion_complete'] = True
            print("✓ Fusion complete\n")
            
            # STAGE 2: OCR Extraction
            print("STAGE 2: OCR Extraction")
            print("-" * 70)
            
            ocr_input = os.path.join(inspection_dir, 'final_ocr_input.png')
            
            if not os.path.exists(ocr_input):
                raise FileNotFoundError(f"Fusion output not found: {ocr_input}")
            
            ocr_result = self.ocr_system.extract_wagon_number(ocr_input, inspection_dir)
            
            result['ocr_complete'] = True
            result['wagon_number'] = ocr_result['wagon_number']
            result['ocr_confidence'] = ocr_result['confidence']
            result['is_readable'] = ocr_result['is_valid']
            
            # STAGE 3: Quality Assessment
            print("\nSTAGE 3: Quality Assessment")
            print("-" * 70)
            
            quality = self._assess_quality(ocr_result)
            result['quality_grade'] = quality['grade']
            result['quality_score'] = quality['score']
            result['quality_issues'] = quality['issues']
            
            print(f"Quality Grade: {quality['grade']}")
            print(f"Quality Score: {quality['score']:.2f}/10")
            if quality['issues']:
                print("Issues:")
                for issue in quality['issues']:
                    print(f"  - {issue}")
            else:
                print("No issues detected")
            
            result['status'] = 'complete'
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            result['status'] = 'error'
            result['error'] = str(e)
        
        # Save metadata
        metadata_path = os.path.join(inspection_dir, 'inspection_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✓ Metadata saved: {metadata_path}")
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _assess_quality(self, ocr_result):
        """
        Assess overall quality of the inspection.
        
        Returns:
            dict with quality metrics
        """
        score = 10.0
        issues = []
        
        # Check if readable
        if ocr_result['wagon_number'] == 'UNREADABLE':
            score -= 5.0
            issues.append("Wagon number unreadable")
        
        # Check confidence
        confidence = ocr_result['confidence']
        
        if confidence < 0.3:
            score -= 3.0
            issues.append(f"Very low confidence ({confidence:.2f})")
        elif confidence < 0.5:
            score -= 2.0
            issues.append(f"Low confidence ({confidence:.2f})")
        elif confidence < 0.7:
            score -= 1.0
            issues.append(f"Moderate confidence ({confidence:.2f})")
        
        # Assign grade
        if score >= 9.0:
            grade = 'A'
        elif score >= 7.0:
            grade = 'B'
        elif score >= 5.0:
            grade = 'C'
        elif score >= 3.0:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': score,
            'grade': grade,
            'issues': issues
        }
    
    def _print_summary(self, result):
        """Print inspection summary."""
        print("\n" + "=" * 70)
        print("INSPECTION SUMMARY")
        print("=" * 70)
        
        print(f"\nInspection ID: {result['inspection_id']}")
        print(f"Status: {result['status'].upper()}")
        
        if result['status'] == 'complete':
            print(f"\nWagon Number: {result['wagon_number']}")
            print(f"OCR Confidence: {result['ocr_confidence']:.3f}")
            print(f"Quality: {result['quality_grade']} ({result['quality_score']:.1f}/10)")
            
            if result['is_readable']:
                print("\n✓ INSPECTION SUCCESSFUL")
            else:
                print("\n⚠ WAGON NUMBER UNREADABLE")
                print("  → Manual inspection required")
        else:
            print(f"\n✗ INSPECTION FAILED")
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        print(f"\nResults: {result['output_dir']}/")
        print("=" * 70)
    
    def batch_inspect(self, wagon_list, output_dir='batch_inspections'):
        """
        Inspect multiple wagons in batch.
        
        Args:
            wagon_list: List of dicts, each with:
                        {'wagon_id': str, 'frames': [paths]}
            output_dir: Base directory for all inspections
            
        Returns:
            List of inspection results
        """
        print("=" * 70)
        print("BATCH INSPECTION")
        print("=" * 70)
        print(f"Total wagons: {len(wagon_list)}")
        print("=" * 70)
        print()
        
        results = []
        
        for i, wagon_info in enumerate(wagon_list):
            print(f"\n[{i+1}/{len(wagon_list)}] Inspecting wagon: {wagon_info.get('wagon_id', 'unknown')}")
            print("-" * 70)
            
            result = self.inspect_wagon(
                frame_paths=wagon_info['frames'],
                wagon_id=wagon_info.get('wagon_id'),
                output_dir=output_dir
            )
            
            results.append(result)
        
        # Summary statistics
        self._print_batch_summary(results)
        
        # Save batch report
        batch_report_path = os.path.join(output_dir, 'batch_report.json')
        with open(batch_report_path, 'w') as f:
            json.dump({
                'total_wagons': len(wagon_list),
                'inspections': results,
                'summary': self._get_batch_stats(results)
            }, f, indent=2)
        
        print(f"\n✓ Batch report saved: {batch_report_path}\n")
        
        return results
    
    def _get_batch_stats(self, results):
        """Calculate batch statistics."""
        total = len(results)
        complete = sum(1 for r in results if r['status'] == 'complete')
        readable = sum(1 for r in results if r.get('is_readable', False))
        
        avg_confidence = sum(r.get('ocr_confidence', 0.0) for r in results) / total if total > 0 else 0.0
        avg_quality = sum(r.get('quality_score', 0.0) for r in results) / total if total > 0 else 0.0
        
        return {
            'total': total,
            'complete': complete,
            'readable': readable,
            'unreadable': complete - readable,
            'failed': total - complete,
            'success_rate': readable / total if total > 0 else 0.0,
            'avg_confidence': avg_confidence,
            'avg_quality_score': avg_quality
        }
    
    def _print_batch_summary(self, results):
        """Print batch summary."""
        stats = self._get_batch_stats(results)
        
        print("\n" + "=" * 70)
        print("BATCH SUMMARY")
        print("=" * 70)
        print(f"\nTotal wagons: {stats['total']}")
        print(f"  ✓ Readable: {stats['readable']}")
        print(f"  ⚠ Unreadable: {stats['unreadable']}")
        print(f"  ✗ Failed: {stats['failed']}")
        print(f"\nSuccess rate: {stats['success_rate']*100:.1f}%")
        print(f"Avg confidence: {stats['avg_confidence']:.3f}")
        print(f"Avg quality: {stats['avg_quality_score']:.1f}/10")
        print("=" * 70)


def example_single_inspection():
    """Example: Single wagon inspection."""
    
    # Initialize system
    system = WagonInspectionSystem(
        fusion_weights='weights/gopro_best.pth',
        ocr_confidence=0.4
    )
    
    # Example frame paths (replace with your actual frames)
    frame_paths = [
        'test_sequence/frame1.jpg',
        'test_sequence/frame2.jpg',
        'test_sequence/frame3.jpg',
        'test_sequence/frame4.jpg',
    ]
    
    # Inspect wagon
    result = system.inspect_wagon(
        frame_paths=frame_paths,
        wagon_id='WAGON_001',
        output_dir='production_inspections'
    )
    
    # Use result
    if result['is_readable']:
        print(f"\n✓ Wagon {result['wagon_number']} inspected successfully")
        # Log to database, trigger next action, etc.
    else:
        print(f"\n⚠ Wagon requires manual inspection")
        # Flag for human review


def example_batch_inspection():
    """Example: Batch inspection of multiple wagons."""
    
    # Initialize system
    system = WagonInspectionSystem(
        fusion_weights='weights/gopro_best.pth',
        ocr_confidence=0.4
    )
    
    # List of wagons to inspect
    wagon_list = [
        {
            'wagon_id': 'WAGON_001',
            'frames': ['data/wagon1/frame1.jpg', 'data/wagon1/frame2.jpg', 
                      'data/wagon1/frame3.jpg']
        },
        {
            'wagon_id': 'WAGON_002',
            'frames': ['data/wagon2/frame1.jpg', 'data/wagon2/frame2.jpg', 
                      'data/wagon2/frame3.jpg', 'data/wagon2/frame4.jpg']
        },
        # ... more wagons
    ]
    
    # Process batch
    results = system.batch_inspect(wagon_list, output_dir='batch_results')
    
    # Process results
    for result in results:
        if result['is_readable']:
            wagon_num = result['wagon_number']
            confidence = result['ocr_confidence']
            # Database insert: INSERT INTO wagons VALUES (wagon_num, confidence, ...)
            print(f"✓ {wagon_num} logged to database")
        else:
            # Flag for manual review
            print(f"⚠ {result['wagon_id']} needs manual review")


if __name__ == '__main__':
    print(__doc__)
    print("\nThis is a template/example file.")
    print("Modify the frame paths and run one of the example functions:")
    print("  - example_single_inspection()")
    print("  - example_batch_inspection()")
    print("\nOr integrate the WagonInspectionSystem class into your application.")
