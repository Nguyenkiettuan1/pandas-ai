# filepath: d:\PandasAI\setup_database.py
"""
Script để khởi tạo database với dữ liệu mẫu hoàn chỉnh
Chạy script này để có ngay dữ liệu để test AI agent
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.dataset import Dataset
from app.models.query import Query
from app.models.conversation import Conversation
from app.core.config import get_settings

settings = get_settings()

# Tạo session factory
SessionLocal = sessionmaker(bind=engine)

class DatabaseSetup:
    """Class để setup database với dữ liệu mẫu"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        self.db.close()
    
    def create_all_tables(self):
        """Tạo tất cả bảng từ models"""
        try:
            print("🏗️  Creating database tables...")
            Base.metadata.create_all(bind=engine)
            
            # Kiểm tra các bảng đã được tạo
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"✅ Created tables: {', '.join(tables)}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    def create_sample_data_tables(self):
        """Tạo bảng dữ liệu mẫu cho business"""
        try:
            print("📊 Creating sample business data tables...")
            
            # 1. Bảng Sales (Doanh số bán hàng)
            sales_sql = """
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(255) NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                amount DECIMAL(12,2) NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price DECIMAL(10,2),
                sale_date DATE NOT NULL,
                region VARCHAR(100),
                salesperson VARCHAR(255),
                commission_rate DECIMAL(5,2) DEFAULT 0.10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 2. Bảng Products (Sản phẩm)
            products_sql = """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                stock_quantity INTEGER DEFAULT 0,
                supplier VARCHAR(255),
                description TEXT,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 3. Bảng Customers (Khách hàng)
            customers_sql = """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                phone VARCHAR(50),
                address TEXT,
                city VARCHAR(100),
                country VARCHAR(100) DEFAULT 'Vietnam',
                customer_type VARCHAR(50) DEFAULT 'individual',
                registration_date DATE DEFAULT CURRENT_DATE,
                total_spent DECIMAL(12,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # 4. Bảng Employees (Nhân viên)
            employees_sql = """
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                position VARCHAR(100),
                department VARCHAR(100),
                salary DECIMAL(10,2),
                hire_date DATE,
                manager_id INTEGER,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # Execute SQL commands
            for sql in [sales_sql, products_sql, customers_sql, employees_sql]:
                self.db.execute(text(sql))
            
            self.db.commit()
            print("✅ Sample business tables created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample tables: {e}")
            self.db.rollback()
            return False
    
    def seed_products_data(self):
        """Thêm dữ liệu sản phẩm mẫu"""
        try:
            print("📦 Seeding products data...")
            
            products_data = [
                # Electronics
                ("Laptop Dell Inspiron 15", "Electronics", 15000000, 12000000, 25, "Dell Vietnam", "Laptop văn phòng hiệu năng cao"),
                ("iPhone 15 Pro Max", "Electronics", 30000000, 25000000, 15, "Apple Store", "Smartphone cao cấp mới nhất"),
                ("Samsung Galaxy S24", "Electronics", 22000000, 18000000, 20, "Samsung Vietnam", "Android flagship"),
                ("MacBook Air M2", "Electronics", 28000000, 23000000, 10, "Apple Store", "Laptop siêu mỏng cho creative"),
                ("iPad Air", "Electronics", 16000000, 13000000, 18, "Apple Store", "Tablet đa năng"),
                
                # Home Appliances  
                ("Tủ lạnh Samsung 360L", "Home Appliances", 12000000, 9500000, 30, "Samsung Vietnam", "Tủ lạnh inverter tiết kiệm điện"),
                ("Máy giặt LG 9kg", "Home Appliances", 8500000, 7000000, 22, "LG Electronics", "Máy giặt cửa trước"),
                ("Điều hòa Daikin 1.5HP", "Home Appliances", 11000000, 8800000, 35, "Daikin Vietnam", "Điều hòa inverter"),
                ("Smart TV Sony 55 inch", "Electronics", 18000000, 14500000, 12, "Sony Vietnam", "Android TV 4K HDR"),
                ("Lò vi sóng Panasonic", "Home Appliances", 2800000, 2200000, 40, "Panasonic Vietnam", "Lò vi sóng 23L"),
                
                # Furniture
                ("Bàn làm việc gỗ sồi", "Furniture", 3500000, 2800000, 15, "Nội thất Hòa Phát", "Bàn gỗ tự nhiên cao cấp"),
                ("Ghế xoay văn phòng", "Furniture", 2200000, 1700000, 25, "Nội thất 190", "Ghế ergonomic thoải mái"),
                ("Tủ sách 5 tầng", "Furniture", 2800000, 2200000, 18, "Nội thất Hòa Phát", "Tủ gỗ MDF phủ melamine"),
                ("Sofa 3 chỗ ngồi", "Furniture", 8500000, 6800000, 8, "Nội thất Xuân Hòa", "Sofa da cao cấp"),
                
                # Sports & Health
                ("Máy chạy bộ điện", "Sports", 12000000, 9500000, 5, "Elip Vietnam", "Máy chạy bộ gia đình"),
                ("Xe đạp thể thao", "Sports", 4500000, 3600000, 12, "Giant Vietnam", "Xe đạp địa hình chuyên nghiệp"),
                ("Bộ tạ tay", "Sports", 1200000, 900000, 30, "Powertec", "Bộ tạ từ 1kg đến 10kg"),
            ]
            
            for product in products_data:
                sql = """
                INSERT INTO products (name, category, price, cost, stock_quantity, supplier, description)
                VALUES (:name, :category, :price, :cost, :stock_quantity, :supplier, :description)
                """
                self.db.execute(text(sql), {
                    'name': product[0],
                    'category': product[1], 
                    'price': product[2],
                    'cost': product[3],
                    'stock_quantity': product[4],
                    'supplier': product[5],
                    'description': product[6]
                })
            
            self.db.commit()
            print(f"✅ Added {len(products_data)} products")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding products: {e}")
            self.db.rollback()
            return False
    
    def seed_customers_data(self):
        """Thêm dữ liệu khách hàng mẫu"""
        try:
            print("👥 Seeding customers data...")
            
            customers_data = [
                ("Công ty TNHH ABC", "abc@company.com", "0901234567", "123 Nguyễn Huệ, Q1", "TP.HCM", "Vietnam", "corporate"),
                ("Nguyễn Văn An", "an.nguyen@email.com", "0907654321", "456 Lê Lợi, Q1", "TP.HCM", "Vietnam", "individual"),
                ("Công ty XYZ Limited", "contact@xyz.com", "0912345678", "789 Trần Hưng Đạo, Ba Đình", "Hà Nội", "Vietnam", "corporate"),
                ("Trần Thị Bình", "binh.tran@gmail.com", "0934567890", "321 Hai Bà Trưng, Q3", "TP.HCM", "Vietnam", "individual"),
                ("Tập đoàn DEF", "info@def.com.vn", "0945678901", "654 Kim Mã, Ba Đình", "Hà Nội", "Vietnam", "corporate"),
                ("Lê Văn Cường", "cuong.le@yahoo.com", "0956789012", "987 Ngô Quyền, Hải Châu", "Đà Nẵng", "Vietnam", "individual"),
                ("Công ty Cổ phần GHI", "sales@ghi.vn", "0967890123", "147 Nguyễn Thái Học, Q1", "TP.HCM", "Vietnam", "corporate"),
                ("Phạm Thị Dung", "dung.pham@hotmail.com", "0978901234", "258 Bạch Đằng, Hai Bà Trưng", "Hà Nội", "Vietnam", "individual"),
                ("Doanh nghiệp JKL", "admin@jkl.com", "0989012345", "369 Lý Thường Kiệt, Hải Châu", "Đà Nẵng", "Vietnam", "corporate"),
                ("Hoàng Văn Em", "em.hoang@gmail.com", "0990123456", "741 Trường Chinh, Tân Bình", "TP.HCM", "Vietnam", "individual"),
            ]
            
            for customer in customers_data:
                sql = """
                INSERT INTO customers (name, email, phone, address, city, country, customer_type)
                VALUES (:name, :email, :phone, :address, :city, :country, :customer_type)
                """
                self.db.execute(text(sql), {
                    'name': customer[0],
                    'email': customer[1],
                    'phone': customer[2], 
                    'address': customer[3],
                    'city': customer[4],
                    'country': customer[5],
                    'customer_type': customer[6]
                })
            
            self.db.commit()
            print(f"✅ Added {len(customers_data)} customers")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding customers: {e}")
            self.db.rollback()
            return False
    
    def seed_employees_data(self):
        """Thêm dữ liệu nhân viên mẫu"""
        try:
            print("👨‍💼 Seeding employees data...")
            
            employees_data = [
                ("Nguyễn Minh Quản", "quan.nguyen@company.com", "Giám đốc", "Điều hành", 50000000, "2020-01-15", None),
                ("Trần Thị Lan", "lan.tran@company.com", "Trưởng phòng Sales", "Kinh doanh", 25000000, "2020-03-01", 1),
                ("Lê Văn Hùng", "hung.le@company.com", "Trưởng phòng Marketing", "Marketing", 23000000, "2020-06-15", 1),
                ("Phạm Thị Mai", "mai.pham@company.com", "Kế toán trưởng", "Tài chính", 22000000, "2020-02-10", 1),
                ("Hoàng Văn Nam", "nam.hoang@company.com", "Nhân viên Sales", "Kinh doanh", 15000000, "2021-01-15", 2),
                ("Đỗ Thị Oanh", "oanh.do@company.com", "Nhân viên Sales", "Kinh doanh", 14000000, "2021-03-20", 2),
                ("Vũ Văn Phong", "phong.vu@company.com", "Nhân viên Marketing", "Marketing", 13000000, "2021-07-01", 3),
                ("Bùi Thị Quý", "quy.bui@company.com", "Nhân viên Kế toán", "Tài chính", 12000000, "2021-09-15", 4),
                ("Tạ Văn Sơn", "son.ta@company.com", "Nhân viên Sales", "Kinh doanh", 14500000, "2022-01-10", 2),
                ("Cao Thị Tuyết", "tuyet.cao@company.com", "Chuyên viên Marketing", "Marketing", 16000000, "2022-04-01", 3),
            ]
            
            for employee in employees_data:
                sql = """
                INSERT INTO employees (name, email, position, department, salary, hire_date, manager_id)
                VALUES (:name, :email, :position, :department, :salary, :hire_date, :manager_id)
                """
                self.db.execute(text(sql), {
                    'name': employee[0],
                    'email': employee[1],
                    'position': employee[2],
                    'department': employee[3],
                    'salary': employee[4],
                    'hire_date': employee[5],
                    'manager_id': employee[6]
                })
            
            self.db.commit()
            print(f"✅ Added {len(employees_data)} employees")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding employees: {e}")
            self.db.rollback()
            return False
    
    def seed_sales_data(self):
        """Thêm dữ liệu bán hàng mẫu (3 tháng gần đây)"""
        try:
            print("💰 Seeding sales data...")
            
            # Lấy danh sách products và customers
            products = self.db.execute(text("SELECT id, name, price, category FROM products")).fetchall()
            customers = self.db.execute(text("SELECT id, name FROM customers")).fetchall()
            employees = self.db.execute(text("SELECT id, name FROM employees WHERE department = 'Kinh doanh'")).fetchall()
            
            regions = ["TP.HCM", "Hà Nội", "Đà Nẵng", "Cần Thơ", "Hải Phòng", "Nha Trang", "Vũng Tàu"]
            
            sales_data = []
            
            # Tạo 200 đơn hàng trong 90 ngày qua
            for i in range(200):
                product = random.choice(products)
                customer = random.choice(customers)
                employee = random.choice(employees)
                
                quantity = random.randint(1, 5)
                unit_price = float(product[2])  # Giá gốc từ products
                
                # Có thể có discount 0-20%
                discount = random.uniform(0, 0.2)
                final_unit_price = unit_price * (1 - discount)
                total_amount = final_unit_price * quantity
                
                # Random ngày trong 90 ngày qua
                days_ago = random.randint(0, 90)
                sale_date = datetime.now() - timedelta(days=days_ago)
                
                sales_data.append({
                    'customer_name': customer[1],
                    'product_name': product[1],
                    'category': product[3],
                    'amount': total_amount,
                    'quantity': quantity,
                    'unit_price': final_unit_price,
                    'sale_date': sale_date.date(),
                    'region': random.choice(regions),
                    'salesperson': employee[1],
                    'commission_rate': random.uniform(0.05, 0.15)
                })
            
            # Bulk insert
            for sale in sales_data:
                sql = """
                INSERT INTO sales 
                (customer_name, product_name, category, amount, quantity, unit_price, 
                 sale_date, region, salesperson, commission_rate)
                VALUES 
                (:customer_name, :product_name, :category, :amount, :quantity, :unit_price,
                 :sale_date, :region, :salesperson, :commission_rate)
                """
                self.db.execute(text(sql), sale)
            
            self.db.commit()
            print(f"✅ Added {len(sales_data)} sales records")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding sales: {e}")
            self.db.rollback()
            return False
    
    def create_dataset_records(self):
        """Tạo dataset records cho PandasAI agent"""
        try:
            print("📚 Creating dataset records for AI agent...")
            
            # Connection string cho local database
            connection_string = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            
            datasets = [
                Dataset(
                    name="Sales Analytics",
                    description="Dữ liệu phân tích bán hàng - doanh số, sản phẩm, khách hàng theo thời gian",
                    connection_string=connection_string,
                    table_name="sales"
                ),
                Dataset(
                    name="Product Catalog",
                    description="Danh mục sản phẩm - giá cả, tồn kho, nhà cung cấp",
                    connection_string=connection_string,
                    table_name="products"
                ),
                Dataset(
                    name="Customer Database",
                    description="Cơ sở dữ liệu khách hàng - thông tin liên lạc, địa chỉ, loại khách hàng",
                    connection_string=connection_string,
                    table_name="customers"
                ),
                Dataset(
                    name="Employee Records",
                    description="Hồ sơ nhân viên - thông tin cá nhân, chức vụ, lương bổng",
                    connection_string=connection_string,
                    table_name="employees"
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
    
    def create_sample_queries(self):
        """Tạo một số query mẫu để demo"""
        try:
            print("🔍 Creating sample queries...")
            
            sample_queries = [
                Query(
                    question="Tổng doanh thu tháng này là bao nhiêu?",
                    sql_query="SELECT SUM(amount) FROM sales WHERE DATE_PART('month', sale_date) = DATE_PART('month', CURRENT_DATE)",
                    result_summary="Tổng doanh thu tháng này: 2,450,000,000 VND",
                    execution_time=0.23,
                    dataset_id=1,
                    profile_name="sales_specialist"
                ),
                Query(
                    question="Top 5 sản phẩm bán chạy nhất?",
                    sql_query="SELECT product_name, SUM(quantity) as total_sold FROM sales GROUP BY product_name ORDER BY total_sold DESC LIMIT 5",
                    result_summary="Top 5: iPhone 15 Pro Max (45 chiếc), Laptop Dell (38 chiếc), Samsung Galaxy (32 chiếc), MacBook Air (28 chiếc), iPad Air (25 chiếc)",
                    execution_time=0.18,
                    dataset_id=1,
                    profile_name="sales_specialist"
                ),
                Query(
                    question="Sản phẩm nào còn ít hàng nhất?",
                    sql_query="SELECT name, stock_quantity FROM products WHERE status = 'active' ORDER BY stock_quantity ASC LIMIT 10",
                    result_summary="Sản phẩm ít hàng nhất: Máy chạy bộ điện (5 chiếc), Sofa 3 chỗ ngồi (8 chiếc), MacBook Air M2 (10 chiếc)",
                    execution_time=0.15,
                    dataset_id=2,
                    profile_name="general_analyst"
                )
            ]
            
            for query in sample_queries:
                self.db.add(query)
            
            self.db.commit()
            print(f"✅ Created {len(sample_queries)} sample queries")
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample queries: {e}")
            self.db.rollback()
            return False
    
    def verify_setup(self):
        """Kiểm tra và in thống kê dữ liệu đã tạo"""
        try:
            print("\n📊 Database Setup Verification:")
            print("=" * 50)
            
            # Đếm records trong từng bảng
            tables = ['products', 'customers', 'employees', 'sales', 'datasets', 'queries']
            
            for table in tables:
                try:
                    result = self.db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"✅ {table.capitalize()}: {result} records")
                except:
                    print(f"⚠️  {table.capitalize()}: Table not found or empty")
            
            # Test queries mẫu
            print("\n🧪 Sample Query Tests:")
            print("-" * 30)
            
            test_queries = [
                ("Total Sales Today", "SELECT COUNT(*) as orders_today FROM sales WHERE sale_date = CURRENT_DATE"),
                ("Total Revenue This Month", "SELECT SUM(amount) as monthly_revenue FROM sales WHERE DATE_PART('month', sale_date) = DATE_PART('month', CURRENT_DATE)"),
                ("Products in Stock", "SELECT COUNT(*) as products_in_stock FROM products WHERE stock_quantity > 0"),
                ("Active Customers", "SELECT COUNT(*) as active_customers FROM customers")
            ]
            
            for name, query in test_queries:
                try:
                    result = self.db.execute(text(query)).scalar()
                    print(f"✅ {name}: {result}")
                except Exception as e:
                    print(f"❌ {name}: Error - {e}")
            
            print("\n🎉 Database setup completed successfully!")
            print("💡 You can now test the AI agent with questions like:")
            print("   - 'Doanh thu tháng này là bao nhiêu?'")
            print("   - 'Top 5 sản phẩm bán chạy nhất?'")
            print("   - 'Khách hàng nào mua nhiều nhất?'")
            print("   - 'Nhân viên sales nào có doanh số cao nhất?'")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in verification: {e}")
            return False

def main():
    """Main function để chạy toàn bộ setup"""
    print("🚀 Starting Database Setup for PandasAI Q&A System")
    print("=" * 60)
    
    setup = DatabaseSetup()
    
    steps = [
        ("Creating tables", setup.create_all_tables),
        ("Creating sample data tables", setup.create_sample_data_tables),
        ("Seeding products", setup.seed_products_data),
        ("Seeding customers", setup.seed_customers_data),
        ("Seeding employees", setup.seed_employees_data),
        ("Seeding sales", setup.seed_sales_data),
        ("Creating datasets", setup.create_dataset_records),
        ("Creating sample queries", setup.create_sample_queries),
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
        print("1. Start the server: python main.py")
        print("2. Open browser: http://localhost:8000/docs")
        print("3. Test the AI agent with sample questions!")
    else:
        print("\n💥 Setup failed. Please check the errors above.")
        sys.exit(1)
