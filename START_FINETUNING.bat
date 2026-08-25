@echo off
REM Fine-tune MIMOUNetPlus model
REM Quick start script

echo ========================================
echo MIMOUNetPlus Fine-tuning Script
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Starting fine-tuning...
echo Dataset: train/train/ (1066 pairs)
echo.

REM Start training with default settings
python finetune_mimo.py ^
    --train_blur train/train/blur ^
    --train_sharp train/train/sharp ^
    --batch_size 4 ^
    --patch_size 256 ^
    --epochs 50 ^
    --lr 0.0001 ^
    --val_split 0.1 ^
    --save_dir checkpoints ^
    --num_workers 4

echo.
echo ========================================
echo Training completed!
echo Check checkpoints/ for saved models
echo ========================================
pause
