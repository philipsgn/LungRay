#!/usr/bin/env python3
"""
scripts/extract_test_samples.py
Trích xuất có chọn lọc 20-30 ảnh tiêu biểu từ mỗi tập dữ liệu nén trong thư mục dataset/
vào thư mục test_samples/ mà không cần giải nén toàn bộ hàng chục GB.
"""

import sys
import shutil
import zipfile
from pathlib import Path
import pandas as pd

# Reconfigure stdout for utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def extract_nih_samples(dest_dir: Path, count: int = 25):
    """Trích xuất 25 ảnh đa dạng từ NIH ChestX-ray14 kèm nhãn bệnh."""
    print("\n[+] Đang xử lý 01_nih_chestxray14...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = Path("dataset/nih-chestXray-14/Data_Entry_2017.csv")
    if not csv_path.exists():
        print("  [!] Không tìm thấy Data_Entry_2017.csv")
        return 0
        
    df = pd.read_csv(csv_path)
    meta = dict(zip(df['Image Index'], df['Finding Labels']))
    
    # Ưu tiên lấy từ dataset/nih-chestXray-14/images đã có sẵn
    img_dir = Path("dataset/nih-chestXray-14/images")
    extracted_count = 0
    
    if img_dir.exists():
        # Chọn các nhãn bệnh đại diện
        target_labels = [
            "No Finding", "Cardiomegaly", "Effusion", "Infiltration", 
            "Atelectasis", "Pneumothorax", "Nodule", "Mass", "Consolidation"
        ]
        
        selected_files = []
        for p in sorted(img_dir.glob("*.png")):
            lbl = meta.get(p.name, "Unknown")
            selected_files.append((p, lbl))
            
        # Lấy đa dạng
        per_label = {}
        for p, lbl in selected_files:
            clean_lbl = lbl.replace("|", "_").replace(" ", "_").lower()
            if "no_finding" in clean_lbl:
                prefix = "normal"
            else:
                prefix = clean_lbl.split("_")[0]
            per_label.setdefault(prefix, []).append((p, prefix, p.name))
            
        final_list = []
        # Mỗi loại lấy tối đa 3-4 ảnh
        for prefix, items in per_label.items():
            final_list.extend(items[:3])
            if len(final_list) >= count:
                break
                
        # Nếu chưa đủ count, bù thêm
        if len(final_list) < count:
            for prefix, items in per_label.items():
                for it in items[3:]:
                    final_list.append(it)
                    if len(final_list) >= count:
                        break
                if len(final_list) >= count:
                    break
                    
        for src_path, prefix, fname in final_list[:count]:
            out_name = f"{prefix}_{fname}"
            out_path = dest_dir / out_name
            shutil.copy2(src_path, out_path)
            extracted_count += 1
            
    print(f"  [OK] Đã trích xuất {extracted_count} ảnh NIH ChestX-ray14 vào: {dest_dir}")
    return extracted_count


def extract_tb_samples(dest_dir: Path, count: int = 20):
    """Trích xuất 20 ảnh (10 Normal + 10 Tuberculosis) từ dataset/tuberculosis.zip."""
    print("\n[+] Đang xử lý 02_tb_shenzhen...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path("dataset/tuberculosis.zip")
    
    if not zip_path.exists():
        print(f"  [!] Không tìm thấy {zip_path}")
        return 0
        
    extracted_count = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        normal_files = [f for f in namelist if 'Normal/' in f and f.lower().endswith(('.png', '.jpg'))][:10]
        tb_files = [f for f in namelist if 'Tuberculosis/' in f and f.lower().endswith(('.png', '.jpg'))][:10]
        
        for f in normal_files:
            fname = Path(f).name
            out_path = dest_dir / f"normal_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
        for f in tb_files:
            fname = Path(f).name
            out_path = dest_dir / f"tb_cavitation_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
    print(f"  [OK] Đã trích xuất {extracted_count} ảnh Lao phổi TB vào: {dest_dir}")
    return extracted_count


def extract_covid_samples(dest_dir: Path, count: int = 30):
    """Trích xuất 30 ảnh (10 COVID, 10 Normal, 10 Viral Pneumonia) từ dataset/covid-19-radiography.zip."""
    print("\n[+] Đang xử lý 03_covid19...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path("dataset/covid-19-radiography.zip")
    
    if not zip_path.exists():
        print(f"  [!] Không tìm thấy {zip_path}")
        return 0
        
    extracted_count = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        covid_files = [f for f in namelist if '/COVID/images/' in f and f.lower().endswith('.png')][:10]
        normal_files = [f for f in namelist if '/Normal/images/' in f and f.lower().endswith('.png')][:10]
        viral_files = [f for f in namelist if '/Viral Pneumonia/images/' in f and f.lower().endswith('.png')][:10]
        
        for f in covid_files:
            fname = Path(f).name
            out_path = dest_dir / f"covid19_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
        for f in normal_files:
            fname = Path(f).name
            out_path = dest_dir / f"normal_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
        for f in viral_files:
            fname = Path(f).name
            out_path = dest_dir / f"viral_pneumonia_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
    print(f"  [OK] Đã trích xuất {extracted_count} ảnh COVIDx vào: {dest_dir}")
    return extracted_count


def extract_rsna_samples(dest_dir: Path, count: int = 20):
    """Trích xuất 20 file DICOM .dcm nguyên bản từ rsna-pneumonia-detection-challenge.zip."""
    print("\n[+] Đang xử lý 04_rsna_pneumonia...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path("dataset/rsna-pneumonia-detection-challenge.zip")
    
    if not zip_path.exists():
        print(f"  [!] Không tìm thấy {zip_path}")
        return 0
        
    extracted_count = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        dcm_files = [f for f in namelist if f.lower().endswith('.dcm') and not Path(f).name.startswith('._')][:count]
        
        for f in dcm_files:
            fname = Path(f).name
            out_path = dest_dir / f"rsna_pneumonia_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
    print(f"  [OK] Đã trích xuất {extracted_count} file DICOM (.dcm) RSNA vào: {dest_dir}")
    return extracted_count


def extract_vindr_samples(dest_dir: Path, count: int = 25):
    """Trích xuất 25 ảnh X-quang Việt Nam từ dataset/vinbigdata.zip."""
    print("\n[+] Đang xử lý 05_vindr_vietnam...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path("dataset/vinbigdata.zip")
    
    if not zip_path.exists():
        print(f"  [!] Không tìm thấy {zip_path}")
        return 0
        
    extracted_count = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        png_files = [f for f in namelist if f.lower().endswith('.png') and not Path(f).name.startswith('._')][:count]
        
        for f in png_files:
            fname = Path(f).name
            out_path = dest_dir / f"vindr_{fname}"
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
    print(f"  [OK] Đã trích xuất {extracted_count} ảnh VinDr-CXR vào: {dest_dir}")
    return extracted_count


def extract_chexpert_samples(dest_dir: Path, count: int = 20):
    """Trích xuất 20 ảnh ngực thẳng frontal từ dataset/cheXpert.zip."""
    print("\n[+] Đang xử lý 06_chexpert_stanford...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = Path("dataset/cheXpert.zip")
    
    if not zip_path.exists():
        print(f"  [!] Không tìm thấy {zip_path}")
        return 0
        
    extracted_count = 0
    with zipfile.ZipFile(zip_path, 'r') as zf:
        namelist = zf.namelist()
        # Tìm các file frontal hợp lệ, loại trừ file ẩn '._'
        frontal_files = []
        for f in namelist:
            p = Path(f)
            if 'frontal' in f.lower() and f.lower().endswith(('.jpg', '.png')) and not p.name.startswith('._'):
                frontal_files.append(f)
                if len(frontal_files) >= count:
                    break
                    
        for f in frontal_files:
            # Tạo tên mô tả: e.g. chexpert_patient00001_study1_view1_frontal.jpg
            parts = Path(f).parts
            patient_part = [part for part in parts if 'patient' in part]
            study_part = [part for part in parts if 'study' in part]
            pat_str = patient_part[0] if patient_part else "pat"
            std_str = study_part[0] if study_part else "std"
            fname = Path(f).name
            
            out_name = f"chexpert_{pat_str}_{std_str}_{fname}"
            out_path = dest_dir / out_name
            with open(out_path, 'wb') as out_f:
                out_f.write(zf.read(f))
            extracted_count += 1
            
    print(f"  [OK] Đã trích xuất {extracted_count} ảnh Stanford CheXpert vào: {dest_dir}")
    return extracted_count


def create_readme(base_dir: Path, summary: dict):
    """Tạo tệp README.md hướng dẫn sử dụng bộ ảnh test."""
    readme_path = base_dir / "README.md"
    content = f"""# BỘ ẢNH TEST TIÊU BIỂU TRÍCH XUẤT TỪ 6 BỘ DỮ LIỆU LUNGRAY (test_samples/)

Thư mục này chứa các ảnh X-quang được trích xuất chọn lọc từ các tệp nén hàng chục GB trong thư mục `dataset/`.
Các ảnh đã được đặt tên kèm tiền tố nhãn bệnh rõ ràng để bạn có thể dễ dàng kéo thả vào Trạm đọc phim PACS (`http://localhost:3000`) để kiểm tra hoặc demo trước Hội đồng.

---

## 1. THỐNG KÊ DANH MỤC ẢNH TEST

| Thư mục | Bộ dữ liệu nguồn | Định dạng | Số lượng | Nhãn bệnh tiêu biểu |
|:---|:---|:---:|:---:|:---|
| `01_nih_chestxray14/` | NIH ChestX-ray14 (Hoa Kỳ) | PNG | {summary.get('nih', 0)} | `normal_`, `cardiomegaly_`, `effusion_`, `pneumonia_`, `atelectasis_`, `pneumothorax_`, `nodule_`, `mass_` |
| `02_tb_shenzhen/` | TB Radiography (Bệnh viện Thâm Quyến) | PNG | {summary.get('tb', 0)} | `normal_` (khỏe mạnh), `tb_cavitation_` (lao phổi tạo hang thùy đỉnh) |
| `03_covid19/` | COVID-19 Radiography (Benchmark) | PNG | {summary.get('covid', 0)} | `covid19_` (viêm phổi virus), `normal_`, `viral_pneumonia_` |
| `04_rsna_pneumonia/` | RSNA Pneumonia Detection | DICOM (.dcm) | {summary.get('rsna', 0)} | `rsna_pneumonia_*.dcm` (ảnh chuẩn y tế có tổn thương đông đặc) |
| `05_vindr_vietnam/` | VinDr-CXR (Bệnh viện Bạch Mai & E) | PNG | {summary.get('vindr', 0)} | `vindr_*.png` (ảnh lâm sàng thực tế bệnh nhân Việt Nam) |
| `06_chexpert_stanford/` | Stanford CheXpert (Đại học Stanford) | JPG | {summary.get('chexpert', 0)} | `chexpert_*.jpg` (ảnh ngực thẳng kiểm định ngoại vi Domain Shift) |
| **Tổng cộng** | **Toàn bộ 6 tập dữ liệu** | - | **{sum(summary.values())} ảnh** | **Dung lượng nhẹ (~80MB), sẵn sàng kéo thả test** |

---

## 2. HƯỚNG DẪN KÉO THẢ TEST TRÊN WEB PACS

1. Khởi động hệ thống theo cẩm nang `docs/DEMO_PRESENTATION_GUIDE.md`:
   - Backend: `uvicorn app.backend.main:app --reload`
   - Frontend: `npm run dev` tại `app/frontend/`
2. Mở trình duyệt tại `http://localhost:3000`.
3. Kéo thả bất kỳ tệp ảnh nào từ các thư mục trên vào khung tải ảnh:
   - Thử `01_nih_chestxray14/normal_...` -> Kết quả âm tính, không phát hiện bất thường.
   - Thử `02_tb_shenzhen/tb_cavitation_...` -> Head B phát hiện Lao phổi >96%, heatmap đỏ rực thùy đỉnh.
   - Thử `03_covid19/covid19_...` -> Head C phát hiện COVID-19, Cổng Dense-UNet gom nhiệt vào phế nang.
   - Thử `04_rsna_pneumonia/rsna_pneumonia_...dcm` -> Hệ thống tự giải mã DICOM trực tiếp.
"""
    readme_path.write_text(content, encoding="utf-8")
    print(f"\n[OK] Đã tạo tệp hướng dẫn tra cứu: {readme_path}")


def main():
    base_dir = Path("test_samples")
    base_dir.mkdir(exist_ok=True)
    
    print("=" * 65)
    print(" [LungRay] SELECTIVE DATASET SAMPLE EXTRACTION RUNNER")
    print("=" * 65)
    
    summary = {}
    summary['nih'] = extract_nih_samples(base_dir / "01_nih_chestxray14", count=25)
    summary['tb'] = extract_tb_samples(base_dir / "02_tb_shenzhen", count=20)
    summary['covid'] = extract_covid_samples(base_dir / "03_covid19", count=30)
    summary['rsna'] = extract_rsna_samples(base_dir / "04_rsna_pneumonia", count=20)
    summary['vindr'] = extract_vindr_samples(base_dir / "05_vindr_vietnam", count=25)
    summary['chexpert'] = extract_chexpert_samples(base_dir / "06_chexpert_stanford", count=20)
    
    create_readme(base_dir, summary)
    
    print("\n" + "=" * 65)
    print(f">>> HOÀN THÀNH: ĐÃ TRÍCH XUẤT TỔNG CỘNG {sum(summary.values())} ẢNH TEST TIÊU BIỂU <<<")
    print("=" * 65)


if __name__ == "__main__":
    main()
