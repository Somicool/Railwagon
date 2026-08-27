"""
Create comprehensive dataset statistics Excel file
Includes: Railway Wagon, GoPro, and LOL datasets
"""
import pandas as pd
from pathlib import Path
import cv2

print("Gathering dataset statistics...")

# Get sample image dimensions
railway_sample = list(Path('train/train/blur').glob('*.jpg'))[0]
railway_img = cv2.imread(str(railway_sample))
railway_h, railway_w, railway_c = railway_img.shape

gopro_sample = list(Path('GOPRO_Large/train').rglob('*.png'))[0]
gopro_img = cv2.imread(str(gopro_sample))
gopro_h, gopro_w, gopro_c = gopro_img.shape

lol_sample = list(Path('LOL_BLUR/train/blur').rglob('*.png'))[0]
lol_img = cv2.imread(str(lol_sample))
lol_h, lol_w, lol_c = lol_img.shape

# Dataset 1: Railway Wagon
railway_data = {
    'Dataset': 'Railway Wagon',
    'Type': 'Motion Deblurring',
    'Total Pairs': 1066,
    'Train Set': 959,
    'Val Set': 107,
    'Test Set': 0,
    'Image Height': railway_h,
    'Image Width': railway_w,
    'Channels': railway_c,
    'Format': 'JPEG',
    'Blur Type': 'Motion blur',
    'Source': 'Railway wagon videos'
}

# Dataset 2: GoPro
gopro_train_count = len(list(Path('GOPRO_Large/train').rglob('*.png'))) // 2
gopro_test_count = len(list(Path('GOPRO_Large/test').rglob('*.png'))) // 2

gopro_data = {
    'Dataset': 'GoPro',
    'Type': 'Motion Deblurring',
    'Total Pairs': gopro_train_count + gopro_test_count,
    'Train Set': gopro_train_count,
    'Val Set': 0,
    'Test Set': gopro_test_count,
    'Image Height': gopro_h,
    'Image Width': gopro_w,
    'Channels': gopro_c,
    'Format': 'PNG',
    'Blur Type': 'Motion blur',
    'Source': 'GoPro camera videos'
}

# Dataset 3: LOL (Low-light)
lol_train_count = len(list(Path('LOL_BLUR/train/blur').rglob('*.png')))
lol_test_count = len(list(Path('LOL_BLUR/test/blur').rglob('*.png')))

lol_data = {
    'Dataset': 'LOL (Low-light)',
    'Type': 'Low-light Enhancement',
    'Total Pairs': lol_train_count + lol_test_count,
    'Train Set': lol_train_count,
    'Val Set': 0,
    'Test Set': lol_test_count,
    'Image Height': lol_h,
    'Image Width': lol_w,
    'Channels': lol_c,
    'Format': 'PNG',
    'Blur Type': 'Low-light/noise',
    'Source': 'Low-light scenes'
}

# Create DataFrame
df_datasets = pd.DataFrame([railway_data, gopro_data, lol_data])

# Summary statistics
total_pairs = df_datasets['Total Pairs'].sum()
total_train = df_datasets['Train Set'].sum()
total_val = df_datasets['Val Set'].sum()
total_test = df_datasets['Test Set'].sum()

summary_data = {
    'Metric': [
        'Total Datasets',
        'Total Image Pairs',
        'Total Training Pairs',
        'Total Validation Pairs',
        'Total Test Pairs',
        'Primary Task',
        'Secondary Task',
        'Training Split',
        'Validation Split',
        'Test Split'
    ],
    'Value': [
        3,
        total_pairs,
        total_train,
        total_val,
        total_test,
        'Motion Deblurring',
        'Low-light Enhancement',
        f'{total_train} ({total_train/total_pairs*100:.1f}%)',
        f'{total_val} ({total_val/total_pairs*100:.1f}%)' if total_val > 0 else '0 (0.0%)',
        f'{total_test} ({total_test/total_pairs*100:.1f}%)'
    ]
}
df_summary = pd.DataFrame(summary_data)

# Create Excel file with multiple sheets
output_file = 'HACKATHON_SUBMISSION/DATASET_STATISTICS.xlsx'
print(f"\nCreating Excel file: {output_file}")

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Sheet 1: Summary
    df_summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Sheet 2: Dataset Details
    df_datasets.to_excel(writer, sheet_name='Dataset Details', index=False)
    
    # Sheet 3: Railway Wagon Detailed
    railway_detailed = {
        'Metric': [
            'Dataset Name',
            'Total Image Pairs',
            'Training Pairs (90%)',
            'Validation Pairs (10%)',
            'Image Resolution',
            'Image Height (px)',
            'Image Width (px)',
            'Channels',
            'Format',
            'Color Space',
            'Bit Depth',
            'Blur Type',
            'Blur Severity',
            'Blur Laplacian Variance',
            'Sharp Laplacian Variance',
            'Sharpness Loss',
            'Source',
            'Location'
        ],
        'Value': [
            'Railway Wagon Dataset',
            1066,
            959,
            107,
            f'{railway_h}×{railway_w}',
            railway_h,
            railway_w,
            railway_c,
            'JPEG',
            'RGB',
            '8-bit (uint8)',
            'Motion blur from moving wagons',
            'Severe (91.7% sharpness loss)',
            67.07,
            808.92,
            '91.7%',
            'Railway wagon video frames',
            'train/train/'
        ]
    }
    df_railway = pd.DataFrame(railway_detailed)
    df_railway.to_excel(writer, sheet_name='Railway Wagon', index=False)
    
    # Sheet 4: GoPro Detailed
    gopro_detailed = {
        'Metric': [
            'Dataset Name',
            'Total Image Pairs',
            'Training Pairs',
            'Test Pairs',
            'Image Resolution',
            'Image Height (px)',
            'Image Width (px)',
            'Channels',
            'Format',
            'Color Space',
            'Blur Type',
            'Source',
            'Location'
        ],
        'Value': [
            'GoPro Motion Deblurring Dataset',
            gopro_train_count + gopro_test_count,
            gopro_train_count,
            gopro_test_count,
            f'{gopro_h}×{gopro_w}',
            gopro_h,
            gopro_w,
            gopro_c,
            'PNG',
            'RGB',
            'Motion blur from camera movement',
            'GoPro camera recordings',
            'GOPRO_Large/'
        ]
    }
    df_gopro = pd.DataFrame(gopro_detailed)
    df_gopro.to_excel(writer, sheet_name='GoPro', index=False)
    
    # Sheet 5: LOL Detailed
    lol_detailed = {
        'Metric': [
            'Dataset Name',
            'Total Image Pairs',
            'Training Pairs',
            'Test Pairs',
            'Image Resolution',
            'Image Height (px)',
            'Image Width (px)',
            'Channels',
            'Format',
            'Color Space',
            'Task Type',
            'Source',
            'Location'
        ],
        'Value': [
            'LOL (Low-light) Dataset',
            lol_train_count + lol_test_count,
            lol_train_count,
            lol_test_count,
            f'{lol_h}×{lol_w}',
            lol_h,
            lol_w,
            lol_c,
            'PNG',
            'RGB',
            'Low-light enhancement',
            'Low-light scenes',
            'LOL_BLUR/'
        ]
    }
    df_lol = pd.DataFrame(lol_detailed)
    df_lol.to_excel(writer, sheet_name='LOL', index=False)

print("\n✓ Excel file created successfully!")
print(f"\nDataset Summary:")
print(f"  Railway Wagon: {1066} pairs")
print(f"  GoPro: {gopro_train_count + gopro_test_count} pairs")
print(f"  LOL: {lol_train_count + lol_test_count} pairs")
print(f"  TOTAL: {total_pairs} pairs")
print(f"\nTraining Split: {total_train} pairs")
print(f"Validation Split: {total_val} pairs")
print(f"Test Split: {total_test} pairs")
