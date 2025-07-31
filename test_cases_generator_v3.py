import os
import re


def auto_generate_test_cases_v3(original_dir, variant_dir):
    """Tự động tạo test cases cho 6 loại variants"""
    test_cases = []
    
    if not os.path.exists(original_dir) or not os.path.exists(variant_dir):
        print("Thư mục không tồn tại!")
        return test_cases
    
    # Lấy danh sách ảnh original
    original_files = [f for f in os.listdir(original_dir) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    print(f"Found {len(original_files)} original images")
    
    # Mapping variants to expected results
    variant_mapping = {
        'identical': 'similar',           # 100% giống
        'minor_changes': 'similar',       # Thay đổi nhỏ
        'text_changes': 'similar',        # Text thay đổi nhưng layout giống
        'layout_changes': 'different',    # Layout thay đổi
        'major_changes': 'different',     # Thay đổi lớn
        'completely_different': 'different'  # Hoàn toàn khác
    }
    
    for original_file in original_files:
        # Extract số từ tên file
        match = re.search(r'original_(\d+)', original_file)
        if not match:
            continue
        
        original_num = match.group(1)
        original_path = os.path.join(original_dir, original_file)
        
        # Tìm thư mục variant tương ứng
        variant_folder = os.path.join(variant_dir, f"original_{original_num}")
        
        if not os.path.exists(variant_folder):
            print(f"Missing variant folder: original_{original_num}")
            continue
        
        # Lấy các variant trong thư mục
        variant_files = [f for f in os.listdir(variant_folder) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        print(f"original_{original_num}: {len(variant_files)} variants")
        
        for variant_file in variant_files:
            variant_path = os.path.join(variant_folder, variant_file)
            
            # Phân loại dựa trên tên file
            variant_name = variant_file.split('.')[0]  # Remove extension
            expected = variant_mapping.get(variant_name, "unknown")
            
            test_cases.append((original_path, variant_path, expected))
    
    return test_cases
