#!/usr/bin/env python3
"""
YOLOv8 Multi-Class Deer Training Script
Sprint 4: Sex/Age Classification Model Training

Trains YOLOv8 on Roboflow Whitetail Deer v46 dataset with 11 classes:
- Deer classes: doe, fawn, mature, mid, young
- Other: UTV, cow, coyote, person, raccoon, turkey

Training Configuration:
- Model: YOLOv8n (nano - fastest, 3M params)
- GPU: CUDA enabled (RTX 4080 Super)
- Batch size: 16 (adjust based on GPU memory)
- Epochs: 100 (with early stopping)
- Image size: 640x640
- Optimizer: AdamW
- Data augmentation: Enabled by default

Expected Training Time:
- With RTX 4080 Super: ~2-4 hours for 100 epochs
- ~1-2 minutes per epoch with batch size 16

Usage:
    python3 scripts/train_multiclass_model.py

    Optional arguments:
    --epochs 100       Number of training epochs
    --batch 16         Batch size
    --imgsz 640        Image size
    --model yolov8n    Model size (n, s, m, l, x)
    --device 0         GPU device (0, 1, etc)
    --patience 20      Early stopping patience
"""

import argparse
import sys
from pathlib import Path
import torch
from ultralytics import YOLO


def check_gpu():
    """Check GPU availability and print info."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"[OK] GPU Available: {gpu_name}")
        print(f"[OK] GPU Memory: {gpu_memory:.1f} GB")
        return True
    else:
        print("[WARN] No GPU detected - training will be VERY slow on CPU")
        print("[WARN] Recommend using GPU for this training job")
        response = input("Continue on CPU anyway? (y/n): ")
        return response.lower() == 'y'


def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 Multi-Class Deer Model')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size')
    parser.add_argument('--model', type=str, default='yolov8n',
                       choices=['yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x'],
                       help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--device', type=int, default=0, help='GPU device ID')
    parser.add_argument('--patience', type=int, default=20,
                       help='Early stopping patience (epochs without improvement)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume training from last checkpoint')

    args = parser.parse_args()

    # Project paths
    project_root = Path(__file__).parent.parent
    data_yaml = project_root / 'src/models/training_data/deer_multiclass.yaml'
    output_dir = project_root / 'src/models/runs'

    # Verify data config exists
    if not data_yaml.exists():
        print(f"[FAIL] Data config not found: {data_yaml}")
        sys.exit(1)

    print("="*70)
    print("YOLOv8 MULTI-CLASS DEER TRAINING")
    print("="*70)
    print(f"Model:        {args.model}.pt")
    print(f"Dataset:      {data_yaml}")
    print(f"Epochs:       {args.epochs}")
    print(f"Batch Size:   {args.batch}")
    print(f"Image Size:   {args.imgsz}x{args.imgsz}")
    print(f"Device:       cuda:{args.device}")
    print(f"Patience:     {args.patience} epochs")
    print(f"Output:       {output_dir}")
    print("="*70)
    print()

    # Check GPU
    if not check_gpu():
        print("[FAIL] GPU check failed - exiting")
        sys.exit(1)

    print()
    print("[INFO] Loading pretrained model...")

    # Load pretrained model (COCO weights for transfer learning)
    model = YOLO(f'{args.model}.pt')

    print("[OK] Model loaded successfully")
    print()
    print("[INFO] Starting training...")
    print("[INFO] Training progress will be displayed below")
    print("[INFO] Press Ctrl+C to stop training gracefully")
    print()

    # Training hyperparameters
    train_args = {
        'data': str(data_yaml),
        'epochs': args.epochs,
        'imgsz': args.imgsz,
        'batch': args.batch,
        'device': args.device,
        'patience': args.patience,
        'save': True,
        'save_period': 10,  # Save checkpoint every 10 epochs
        'project': str(output_dir),
        'name': 'deer_multiclass',
        'exist_ok': True,
        'pretrained': True,
        'optimizer': 'AdamW',
        'verbose': True,
        'seed': 42,
        'deterministic': False,  # Faster training
        'single_cls': False,  # Multi-class mode
        'rect': False,  # Use square images
        'cos_lr': True,  # Cosine learning rate scheduler
        'close_mosaic': 10,  # Disable mosaic augmentation last 10 epochs
        'resume': args.resume,
        'amp': True,  # Automatic Mixed Precision (faster on modern GPUs)
        'fraction': 1.0,  # Use 100% of training data
        'profile': False,  # Disable profiling for speed
        'freeze': None,  # Don't freeze any layers
        'lr0': 0.01,  # Initial learning rate
        'lrf': 0.01,  # Final learning rate (fraction of lr0)
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3.0,
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.1,
        'box': 7.5,  # Box loss gain
        'cls': 0.5,  # Class loss gain
        'dfl': 1.5,  # DFL loss gain
        'plots': True,  # Save training plots
        'val': True,  # Validate during training
    }

    try:
        # Train the model
        results = model.train(**train_args)

        print()
        print("="*70)
        print("[OK] TRAINING COMPLETE!")
        print("="*70)
        print(f"Best model saved to: {output_dir}/deer_multiclass/weights/best.pt")
        print(f"Last model saved to: {output_dir}/deer_multiclass/weights/last.pt")
        print()
        print("Training Metrics:")
        print(f"  Final mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
        print(f"  Final mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")
        print()
        print("Next Steps:")
        print("  1. Review training plots in: {}/deer_multiclass/".format(output_dir))
        print("  2. Validate model: python3 scripts/validate_model.py")
        print("  3. Test on images: python3 scripts/test_detection.py")
        print("="*70)

    except KeyboardInterrupt:
        print()
        print("[WARN] Training interrupted by user")
        print(f"[INFO] Checkpoint saved to: {output_dir}/deer_multiclass/weights/last.pt")
        print("[INFO] Resume training with: --resume flag")
        sys.exit(0)

    except Exception as e:
        print()
        print(f"[FAIL] Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
