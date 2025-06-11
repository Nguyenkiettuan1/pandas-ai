# filepath: d:\PandasAI\setup_business_data.py
"""
Script để tạo dữ liệu doanh nghiệp mẫu cho demo Q&A system
Bao gồm: nhân viên, hóa đơn, khách hàng, sản phẩm với tiếng Việt
"""

import sys
import os
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, create_engine
from app.core.database import engine, Base
from app.models.dataset import Dataset
from app.core.config import settings

SessionLocal = sessionmaker(bind=engine)

class BusinessDataSetup:
    """Class để setup dữ liệu doanh nghiệp mẫu"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        self.db.close()
    
    def create_business_tables(self):
        """Tạo các bảng dữ liệu doanh nghiệp"""
        try:
            print("🏗️ Creating business tables...")
            
            # 1. Bảng Nhân viên
            employees_sql = """
            CREATE TABLE IF NOT EXISTS nhan_vien (
                ma_nv VARCHAR(20) PRIMARY KEY,
                ho_ten VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                sdt VARCHAR(20),
                chuc_vu VARCHAR(100),
                phong_ban VARCHAR(100),
                luong DECIMAL(12,2),
                ngay_vao_lam DATE,
                dia_chi TEXT,
                ngay_sinh DATE,
                gioi_tinh VARCHAR(10),
                trang_thai VARCHAR(20) DEFAULT 'Đang làm việc',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 2. Bảng Khách hàng
            customers_sql = """
            CREATE TABLE IF NOT EXISTS khach_hang (
                ma_kh VARCHAR(20) PRIMARY KEY,
                ten_kh VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                sdt VARCHAR(20),
                dia_chi TEXT,
                thanh_pho VARCHAR(100),
                loai_kh VARCHAR(50) DEFAULT 'Cá nhân',
                ngay_dang_ky DATE DEFAULT CURRENT_DATE,
                tong_chi_tieu DECIMAL(15,2) DEFAULT 0,
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 3. Bảng Sản phẩm
            products_sql = """
            CREATE TABLE IF NOT EXISTS san_pham (
                ma_sp VARCHAR(20) PRIMARY KEY,
                ten_sp VARCHAR(255) NOT NULL,
                danh_muc VARCHAR(100),
                gia_ban DECIMAL(12,2) NOT NULL,
                gia_von DECIMAL(12,2),
                ton_kho INTEGER DEFAULT 0,
                don_vi VARCHAR(50) DEFAULT 'Cái',
                nha_cung_cap VARCHAR(255),
                mo_ta TEXT,
                trang_thai VARCHAR(20) DEFAULT 'Đang bán',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 4. Bảng Hóa đơn
            invoices_sql = """
            CREATE TABLE IF NOT EXISTS hoa_don (
                ma_hd VARCHAR(20) PRIMARY KEY,
                ma_kh VARCHAR(20) REFERENCES khach_hang(ma_kh),
                ma_nv VARCHAR(20) REFERENCES nhan_vien(ma_nv),
                ngay_lap DATE NOT NULL,
                tong_tien DECIMAL(15,2) NOT NULL,
                thue DECIMAL(12,2) DEFAULT 0,
                giam_gia DECIMAL(12,2) DEFAULT 0,
                thanh_toan DECIMAL(15,2) NOT NULL,
                phuong_thuc_tt VARCHAR(50) DEFAULT 'Tiền mặt',
                trang_thai VARCHAR(20) DEFAULT 'Đã thanh toán',
                ghi_chu TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 5. Bảng Chi tiết hóa đơn
            invoice_details_sql = """
            CREATE TABLE IF NOT EXISTS chi_tiet_hoa_don (
                id SERIAL PRIMARY KEY,
                ma_hd VARCHAR(20) REFERENCES hoa_don(ma_hd),
                ma_sp VARCHAR(20) REFERENCES san_pham(ma_sp),
                so_luong INTEGER NOT NULL,
                gia_ban DECIMAL(12,2) NOT NULL,
                thanh_tien DECIMAL(15,2) NOT NULL,
                ghi_chu TEXT
            );
            """
              # Execute SQL commands
            for sql in [employees_sql, customers_sql, products_sql, invoices_sql, invoice_details_sql]:
                self.db.execute(text(sql))
            
            self.db.commit()
            print("✅ Business tables created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating business tables: {e}")
            self.db.rollback()
            return False
    
    def seed_employees(self):
        """Thêm dữ liệu nhân viên mẫu"""
        try:
            print("👥 Seeding employees data...")
            
            # Check if employees already exist
            result = self.db.execute(text("SELECT COUNT(*) FROM nhan_vien"))
            count = result.scalar()
            if count > 0:
                print(f"   📋 Found {count} existing employees, skipping seed...")
                return True
            
            employees_data = [
                ("NV001", "Nguyễn Văn An", "an.nguyen@company.com", "0901234567", "Giám đốc", "Điều hành", 50000000, "2020-01-15", "123 Nguyễn Huệ, Q1, TP.HCM", "1985-03-20", "Nam"),
                ("NV002", "Trần Thị Bình", "binh.tran@company.com", "0907654321", "Trưởng phòng", "Kinh doanh", 25000000, "2020-03-01", "456 Lê Lợi, Q3, TP.HCM", "1990-07-15", "Nữ"),
                ("NV003", "Lê Văn Cường", "cuong.le@company.com", "0912345678", "Trưởng phòng", "Kỹ thuật", 23000000, "2020-06-15", "789 Trần Hưng Đạo, Q5, TP.HCM", "1988-11-30", "Nam"),
                ("NV004", "Phạm Thị Dung", "dung.pham@company.com", "0934567890", "Kế toán trưởng", "Tài chính", 22000000, "2020-02-10", "321 Hai Bà Trưng, Q1, TP.HCM", "1987-05-25", "Nữ"),
                ("NV005", "Hoàng Văn Em", "em.hoang@company.com", "0945678901", "Nhân viên", "Kinh doanh", 15000000, "2021-01-15", "654 Nguyễn Thái Học, Q1, TP.HCM", "1995-09-10", "Nam"),
                ("NV006", "Đỗ Thị Phương", "phuong.do@company.com", "0956789012", "Nhân viên", "Kinh doanh", 14000000, "2021-03-20", "987 Bạch Đằng, Q3, TP.HCM", "1992-12-05", "Nữ"),
                ("NV007", "Vũ Văn Giang", "giang.vu@company.com", "0967890123", "Nhân viên", "Kỹ thuật", 13000000, "2021-07-01", "147 Lý Thường Kiệt, Q10, TP.HCM", "1993-04-18", "Nam"),
                ("NV008", "Bùi Thị Hoa", "hoa.bui@company.com", "0978901234", "Nhân viên", "Tài chính", 12000000, "2021-09-15", "258 Cách Mạng Tháng 8, Q3, TP.HCM", "1994-08-22", "Nữ"),
                ("NV009", "Tạ Văn Inh", "inh.ta@company.com", "0989012345", "Nhân viên", "Kinh doanh", 14500000, "2022-01-10", "369 Điện Biên Phủ, Q1, TP.HCM", "1991-01-30", "Nam"),
                ("NV010", "Cao Thị Kim", "kim.cao@company.com", "0990123456", "Chuyên viên", "Marketing", 16000000, "2022-04-01", "741 Trường Chinh, Q12, TP.HCM", "1989-06-14", "Nữ"),
            ]
            
            for emp in employees_data:
                sql = """
                INSERT INTO nhan_vien (ma_nv, ho_ten, email, sdt, chuc_vu, phong_ban, luong, ngay_vao_lam, dia_chi, ngay_sinh, gioi_tinh)
                VALUES (:ma_nv, :ho_ten, :email, :sdt, :chuc_vu, :phong_ban, :luong, :ngay_vao_lam, :dia_chi, :ngay_sinh, :gioi_tinh)
                """
                self.db.execute(text(sql), {
                    'ma_nv': emp[0], 'ho_ten': emp[1], 'email': emp[2], 'sdt': emp[3],
                    'chuc_vu': emp[4], 'phong_ban': emp[5], 'luong': emp[6], 'ngay_vao_lam': emp[7],
                    'dia_chi': emp[8], 'ngay_sinh': emp[9], 'gioi_tinh': emp[10]
                })
            
            self.db.commit()
            print(f"✅ Added {len(employees_data)} employees")
            return True
        except Exception as e:
            print(f"❌ Error seeding employees: {e}")
            self.db.rollback()
            return False
    
    def seed_customers(self):
        """Thêm dữ liệu khách hàng mẫu"""
        try:
            print("🛒 Seeding customers data...")
            
            # Check if customers already exist
            result = self.db.execute(text("SELECT COUNT(*) FROM khach_hang"))
            count = result.scalar()
            if count > 0:
                print(f"   📋 Found {count} existing customers, skipping seed...")
                return True
            
            customers_data = [
                ("KH001", "Công ty TNHH ABC Technology", "contact@abc-tech.com", "0281234567", "123 Nguyễn Văn Cừ, Q5, TP.HCM", "TP.HCM", "Doanh nghiệp"),
                ("KH002", "Võ Thị Lan Anh", "lananh.vo@gmail.com", "0908765432", "456 Cộng Hòa, Q.Tân Bình, TP.HCM", "TP.HCM", "Cá nhân"),
                ("KH003", "Công ty XYZ Solutions", "info@xyz-solutions.vn", "0283456789", "789 Điện Biên Phủ, Q.Bình Thạnh, TP.HCM", "TP.HCM", "Doanh nghiệp"),
                ("KH004", "Nguyễn Minh Tuấn", "minhtuan92@yahoo.com", "0919876543", "321 Lê Văn Sỹ, Q3, TP.HCM", "TP.HCM", "Cá nhân"),
                ("KH005", "Tập đoàn DEF Corp", "sales@def-corp.com.vn", "0284567890", "654 Nguyễn Thị Minh Khai, Q1, TP.HCM", "TP.HCM", "Doanh nghiệp"),
                ("KH006", "Lê Thị Hồng Nhung", "hongnhung.le@outlook.com", "0930987654", "987 Hoàng Văn Thụ, Q.Tân Bình, TP.HCM", "TP.HCM", "Cá nhân"),
                ("KH007", "Công ty GHI Limited", "admin@ghi-ltd.vn", "0285678901", "147 Pasteur, Q1, TP.HCM", "TP.HCM", "Doanh nghiệp"),
                ("KH008", "Trần Quốc Việt", "quocviet.tran@gmail.com", "0941098765", "258 Võ Văn Tần, Q3, TP.HCM", "TP.HCM", "Cá nhân"),
                ("KH009", "Siêu thị JKL Mart", "purchase@jkl-mart.com", "0286789012", "369 Nguyễn Đình Chiểu, Q1, TP.HCM", "TP.HCM", "Doanh nghiệp"),
                ("KH010", "Phạm Văn Long", "vanlong.pham@hotmail.com", "0952109876", "741 Cao Thắng, Q3, TP.HCM", "TP.HCM", "Cá nhân"),
            ]
            
            for cust in customers_data:
                sql = """
                INSERT INTO khach_hang (ma_kh, ten_kh, email, sdt, dia_chi, thanh_pho, loai_kh)
                VALUES (:ma_kh, :ten_kh, :email, :sdt, :dia_chi, :thanh_pho, :loai_kh)
                """
                self.db.execute(text(sql), {
                    'ma_kh': cust[0], 'ten_kh': cust[1], 'email': cust[2], 'sdt': cust[3],
                    'dia_chi': cust[4], 'thanh_pho': cust[5], 'loai_kh': cust[6]
                })
            
            self.db.commit()
            print(f"✅ Added {len(customers_data)} customers")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding customers: {e}")
            self.db.rollback()
            return False
    def seed_products(self):
        """Thêm dữ liệu sản phẩm mẫu"""
        try:
            print("📦 Seeding products data...")
            
            # Check if products already exist
            result = self.db.execute(text("SELECT COUNT(*) FROM san_pham"))
            count = result.scalar()
            if count > 0:
                print(f"   📋 Found {count} existing products, skipping seed...")
                return True
            
            products_data = [
                ("SP001", "Laptop Dell Inspiron 15", "Máy tính", 15000000, 12000000, 50, "Cái", "Dell Vietnam", "Laptop văn phòng cao cấp"),
                ("SP002", "iPhone 15 Pro Max", "Điện thoại", 30000000, 25000000, 30, "Cái", "Apple Store", "Smartphone cao cấp mới nhất"),
                ("SP003", "Samsung Galaxy S24", "Điện thoại", 22000000, 18000000, 25, "Cái", "Samsung Vietnam", "Android flagship"),
                ("SP004", "MacBook Air M2", "Máy tính", 28000000, 23000000, 15, "Cái", "Apple Store", "Laptop siêu mỏng"),
                ("SP005", "iPad Air Gen 5", "Tablet", 16000000, 13000000, 40, "Cái", "Apple Store", "Tablet đa năng"),
                ("SP006", "Smart TV Samsung 55\"", "Điện tử", 18000000, 14500000, 20, "Cái", "Samsung Vietnam", "Smart TV 4K UHD"),
                ("SP007", "Tủ lạnh LG 360L", "Gia dụng", 12000000, 9500000, 35, "Cái", "LG Electronics", "Tủ lạnh inverter"),
                ("SP008", "Máy giặt Electrolux 9kg", "Gia dụng", 8500000, 7000000, 28, "Cái", "Electrolux Vietnam", "Máy giặt cửa trước"),
                ("SP009", "Điều hòa Daikin 1.5HP", "Gia dụng", 11000000, 8800000, 45, "Cái", "Daikin Vietnam", "Điều hòa inverter"),
                ("SP010", "Bàn làm việc gỗ sồi", "Nội thất", 3500000, 2800000, 60, "Cái", "Nội thất Hòa Phát", "Bàn gỗ tự nhiên"),
                ("SP011", "Ghế xoay văn phòng", "Nội thất", 2200000, 1700000, 80, "Cái", "Nội thất 190", "Ghế ergonomic"),
                ("SP012", "Máy in Canon 2900", "Văn phòng", 3000000, 2400000, 25, "Cái", "Canon Vietnam", "Máy in laser"),
            ]
            
            for prod in products_data:
                sql = """
                INSERT INTO san_pham (ma_sp, ten_sp, danh_muc, gia_ban, gia_von, ton_kho, don_vi, nha_cung_cap, mo_ta)
                VALUES (:ma_sp, :ten_sp, :danh_muc, :gia_ban, :gia_von, :ton_kho, :don_vi, :nha_cung_cap, :mo_ta)
                """
                self.db.execute(text(sql), {
                    'ma_sp': prod[0], 'ten_sp': prod[1], 'danh_muc': prod[2], 'gia_ban': prod[3],
                    'gia_von': prod[4], 'ton_kho': prod[5], 'don_vi': prod[6], 
                    'nha_cung_cap': prod[7], 'mo_ta': prod[8]
                })
            
            self.db.commit()
            print(f"✅ Added {len(products_data)} products")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding products: {e}")
            self.db.rollback()
            return False
    def seed_invoices(self):
        """Thêm dữ liệu hóa đơn mẫu"""
        try:
            print("🧾 Seeding invoices data...")
            
            # Check if invoices already exist
            result = self.db.execute(text("SELECT COUNT(*) FROM hoa_don"))
            count = result.scalar()
            if count > 0:
                print(f"   📋 Found {count} existing invoices, skipping seed...")
                return True
            
            # Lấy danh sách mã khách hàng và nhân viên
            customers = self.db.execute(text("SELECT ma_kh FROM khach_hang")).fetchall()
            employees = self.db.execute(text("SELECT ma_nv FROM nhan_vien WHERE phong_ban = 'Kinh doanh'")).fetchall()
            products = self.db.execute(text("SELECT ma_sp, gia_ban FROM san_pham")).fetchall()
            
            # Tạo 20 hóa đơn trong 2 tháng qua
            invoices_data = []
            invoice_details_data = []
            
            for i in range(1, 21):
                ma_hd = f"HD{i:03d}"
                ma_kh = random.choice(customers)[0]
                ma_nv = random.choice(employees)[0]
                
                # Random ngày trong 60 ngày qua
                days_ago = random.randint(0, 60)
                ngay_lap = datetime.now() - timedelta(days=days_ago)
                
                # Tạo chi tiết hóa đơn (1-4 sản phẩm per hóa đơn)
                num_products = random.randint(1, 4)
                selected_products = random.sample(products, num_products)
                
                tong_tien = 0
                
                for prod in selected_products:
                    ma_sp = prod[0]
                    gia_ban = float(prod[1])
                    so_luong = random.randint(1, 3)
                    thanh_tien = gia_ban * so_luong
                    tong_tien += thanh_tien
                    
                    invoice_details_data.append({
                        'ma_hd': ma_hd,
                        'ma_sp': ma_sp,
                        'so_luong': so_luong,
                        'gia_ban': gia_ban,
                        'thanh_tien': thanh_tien
                    })
                
                # Tính thuế và giảm giá
                thue = tong_tien * 0.1  # VAT 10%
                giam_gia = 0
                if tong_tien > 50000000:  # Giảm giá cho đơn hàng lớn
                    giam_gia = tong_tien * 0.05
                
                thanh_toan = tong_tien + thue - giam_gia
                
                phuong_thuc_tt = random.choice(["Tiền mặt", "Chuyển khoản", "Thẻ tín dụng", "Ví điện tử"])
                
                invoices_data.append({
                    'ma_hd': ma_hd,
                    'ma_kh': ma_kh,
                    'ma_nv': ma_nv,
                    'ngay_lap': ngay_lap.date(),
                    'tong_tien': tong_tien,
                    'thue': thue,
                    'giam_gia': giam_gia,
                    'thanh_toan': thanh_toan,
                    'phuong_thuc_tt': phuong_thuc_tt
                })
            
            # Insert hóa đơn
            for invoice in invoices_data:
                sql = """
                INSERT INTO hoa_don (ma_hd, ma_kh, ma_nv, ngay_lap, tong_tien, thue, giam_gia, thanh_toan, phuong_thuc_tt)
                VALUES (:ma_hd, :ma_kh, :ma_nv, :ngay_lap, :tong_tien, :thue, :giam_gia, :thanh_toan, :phuong_thuc_tt)
                """
                self.db.execute(text(sql), invoice)
            
            # Insert chi tiết hóa đơn
            for detail in invoice_details_data:
                sql = """
                INSERT INTO chi_tiet_hoa_don (ma_hd, ma_sp, so_luong, gia_ban, thanh_tien)
                VALUES (:ma_hd, :ma_sp, :so_luong, :gia_ban, :thanh_tien)
                """
                self.db.execute(text(sql), detail)
            
            self.db.commit()
            print(f"✅ Added {len(invoices_data)} invoices with {len(invoice_details_data)} details")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding invoices: {e}")
            self.db.rollback()
            return False
    def create_dataset_records(self):
        """Tạo dataset records cho PandasAI agent"""
        try:
            print("📚 Creating dataset records for AI agent...")
            
            # Check if datasets already exist
            result = self.db.execute(text("SELECT COUNT(*) FROM datasets WHERE table_name IN ('nhan_vien', 'khach_hang', 'san_pham', 'hoa_don', 'chi_tiet_hoa_don')"))
            count = result.scalar()
            if count > 0:
                print(f"   📋 Found {count} existing dataset records, skipping creation...")
                return True
            
            datasets = [
                Dataset(
                    name="Nhân viên", 
                    description="Thông tin nhân viên - mã, tên, chức vụ, phòng ban, lương, liên lạc",
                    table_name="nhan_vien"
                ),
                Dataset(
                    name="Khách hàng",
                    description="Thông tin khách hàng - mã, tên, liên lạc, địa chỉ, loại khách hàng",
                    table_name="khach_hang"
                ),
                Dataset(
                    name="Sản phẩm",
                    description="Danh mục sản phẩm - mã, tên, giá, tồn kho, nhà cung cấp",
                    table_name="san_pham"
                ),
                Dataset(
                    name="Hóa đơn",
                    description="Hóa đơn bán hàng - mã, khách hàng, nhân viên, giá trị, thanh toán",
                    table_name="hoa_don"
                ),
                Dataset(
                    name="Chi tiết hóa đơn",
                    description="Chi tiết hóa đơn - sản phẩm, số lượng, giá, thành tiền",
                    table_name="chi_tiet_hoa_don"
                )
            ]
            
            for dataset in datasets:
                self.db.add(dataset)
            
            self.db.commit()
            print(f"✅ Created {len(datasets)} dataset records")
            
            # In thông tin datasets
            for dataset in datasets:
                print(f"  📊 {dataset.name} (ID: {dataset.id}) -> {dataset.table_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating dataset records: {e}")
            self.db.rollback()
            return False
    
    def verify_setup(self):
        """Kiểm tra dữ liệu đã tạo"""
        try:
            print("\n📊 Business Data Verification:")
            print("=" * 50)
            
            tables = ['nhan_vien', 'khach_hang', 'san_pham', 'hoa_don', 'chi_tiet_hoa_don']
            
            for table in tables:
                try:
                    result = self.db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"✅ {table}: {result} records")
                except:
                    print(f"⚠️  {table}: Table not found")
            
            # Test queries mẫu
            print("\n🧪 Sample Query Tests:")
            print("-" * 30)
            
            test_queries = [
                ("Nhân viên mã NV001", "SELECT ho_ten, chuc_vu FROM nhan_vien WHERE ma_nv = 'NV001'"),
                ("Hóa đơn HD001", "SELECT ma_kh, tong_tien, thanh_toan FROM hoa_don WHERE ma_hd = 'HD001'"),
                ("Sản phẩm máy tính", "SELECT COUNT(*) FROM san_pham WHERE danh_muc = 'Máy tính'"),
                ("Tổng doanh thu", "SELECT SUM(thanh_toan) FROM hoa_don"),
            ]
            
            for name, query in test_queries:
                try:
                    result = self.db.execute(text(query)).fetchone()
                    print(f"✅ {name}: {result}")
                except Exception as e:
                    print(f"❌ {name}: Error - {e}")
            
            print("\n🎉 Business data setup completed successfully!")
            print("💡 You can now ask questions like:")
            print("   - 'Mã nhân viên NV001 là của ai?'")
            print("   - 'Hóa đơn mã HD001 có giá bao nhiêu?'")
            print("   - 'Nhân viên nào ở phòng Kinh doanh?'")
            print("   - 'Sản phẩm nào đang hết hàng?'")
            print("   - 'Khách hàng KH001 là ai?'")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in verification: {e}")
            return False

def main():
    """Main function để chạy toàn bộ setup"""
    print("🚀 Starting Business Data Setup for PandasAI Q&A System")
    print("=" * 60)
    
    setup = BusinessDataSetup()
    
    steps = [
        ("Creating business tables", setup.create_business_tables),
        ("Seeding employees", setup.seed_employees),
        ("Seeding customers", setup.seed_customers),
        ("Seeding products", setup.seed_products),
        ("Seeding invoices", setup.seed_invoices),
        ("Creating datasets", setup.create_dataset_records),
        ("Verifying setup", setup.verify_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"❌ Failed at step: {step_name}")
            return False
        
    print(f"\n✨ All steps completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Next steps:")
        print("1. Cập nhật .env với OpenAI API key hoặc setup local LLM")
        print("2. Start server: python main.py")
        print("3. Test với câu hỏi tiếng Việt!")
    else:
        print("\n💥 Setup failed. Please check the errors above.")
        sys.exit(1)
