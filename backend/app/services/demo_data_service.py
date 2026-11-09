import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.business import Business
from app.models.product import Product
from app.models.customer import Customer, CreditTransaction
from app.models.sale import Sale, SaleItem
from app.models.expense import Expense
from app.models.inventory import InventoryTransaction
from app.utils.security import hash_password

DEMO_USER_EMAIL = "demo@vyaparvoice.in"

class DemoDataService:
    @staticmethod
    def reset_and_seed_demo_data(db: Session) -> dict:
        # 1. Clean existing demo user and cascaded data
        demo_user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if demo_user:
            db.delete(demo_user)
            db.commit()

        # 2. Create demo user
        demo_user = User(
            full_name="Vijay Kumar",
            email=DEMO_USER_EMAIL,
            hashed_password=hash_password("demo12345"),
            phone="9876543210",
            preferred_language="kn"
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        # 3. Create demo business
        business = Business(
            owner_id=demo_user.id,
            business_name="Shree Krishna Kirana & Provisions",
            business_type="Kirana / Grocery",
            GSTIN="29AAAAA0000A1Z5",
            currency="INR",
            timezone="Asia/Kolkata",
            address="#42, 4th Main, Malleshwaram, Bengaluru, Karnataka 560003"
        )
        db.add(business)
        db.commit()
        db.refresh(business)

        # 4. Create 25 Products
        products_data = [
            ("Nandini Milk 500ml", "MILK-500", "Dairy", "pkt", Decimal("22.00"), Decimal("24.00"), Decimal("35.00"), Decimal("10.00")),
            ("Amul Butter 100g", "BUT-100", "Dairy", "pcs", Decimal("48.00"), Decimal("56.00"), Decimal("18.00"), Decimal("5.00")),
            ("Nandini Curd 500g", "CURD-500", "Dairy", "pkt", Decimal("26.00"), Decimal("30.00"), Decimal("20.00"), Decimal("6.00")),
            ("Paneer 200g", "PAN-200", "Dairy", "pkt", Decimal("75.00"), Decimal("90.00"), Decimal("4.00"), Decimal("5.00")), # Low stock
            ("Sona Masoori Rice 25kg", "RICE-25KG", "Grains & Flours", "bag", Decimal("1350.00"), Decimal("1550.00"), Decimal("12.00"), Decimal("3.00")),
            ("Basmati Rice 5kg", "BAS-5KG", "Grains & Flours", "bag", Decimal("420.00"), Decimal("499.00"), Decimal("2.00"), Decimal("5.00")), # Low stock
            ("Aashirvaad Atta 10kg", "ATTA-10KG", "Grains & Flours", "bag", Decimal("390.00"), Decimal("440.00"), Decimal("8.00"), Decimal("4.00")),
            ("Toor Dal 1kg", "DAL-TOOR", "Pulses", "kg", Decimal("145.00"), Decimal("170.00"), Decimal("25.00"), Decimal("5.00")),
            ("Moong Dal 1kg", "DAL-MOONG", "Pulses", "kg", Decimal("110.00"), Decimal("130.00"), Decimal("15.00"), Decimal("5.00")),
            ("Chana Dal 1kg", "DAL-CHANA", "Pulses", "kg", Decimal("85.00"), Decimal("105.00"), Decimal("3.00"), Decimal("5.00")), # Low stock
            ("Fortune Sunflower Oil 1L", "OIL-SUN-1L", "Oils & Ghee", "pkt", Decimal("125.00"), Decimal("145.00"), Decimal("30.00"), Decimal("8.00")),
            ("GRB Ghee 500ml", "GHEE-500", "Oils & Ghee", "jar", Decimal("330.00"), Decimal("380.00"), Decimal("10.00"), Decimal("4.00")),
            ("Mustard Oil 1L", "OIL-MUST-1L", "Oils & Ghee", "btl", Decimal("140.00"), Decimal("165.00"), Decimal("12.00"), Decimal("4.00")),
            ("Tata Salt 1kg", "SALT-1KG", "Spices", "pkt", Decimal("22.00"), Decimal("28.00"), Decimal("45.00"), Decimal("10.00")),
            ("Sugar 1kg", "SUG-1KG", "Spices", "kg", Decimal("38.00"), Decimal("44.00"), Decimal("50.00"), Decimal("15.00")),
            ("Everest Turmeric Powder 100g", "HALDI-100", "Spices", "pkt", Decimal("30.00"), Decimal("38.00"), Decimal("22.00"), Decimal("5.00")),
            ("Red Chilli Powder 200g", "CHILLI-200", "Spices", "pkt", Decimal("65.00"), Decimal("80.00"), Decimal("16.00"), Decimal("5.00")),
            ("Coriander Powder 200g", "DHANIYA-200", "Spices", "pkt", Decimal("55.00"), Decimal("70.00"), Decimal("14.00"), Decimal("5.00")),
            ("Tata Tea Gold 500g", "TEA-500", "Beverages", "pkt", Decimal("290.00"), Decimal("335.00"), Decimal("15.00"), Decimal("4.00")),
            ("Bru Instant Coffee 100g", "COF-100", "Beverages", "jar", Decimal("170.00"), Decimal("200.00"), Decimal("18.00"), Decimal("5.00")),
            ("Parle-G Biscuits 250g", "PARLE-250", "Snacks", "pkt", Decimal("20.00"), Decimal("25.00"), Decimal("60.00"), Decimal("15.00")),
            ("Britannia Good Day 100g", "GOOD-DAY", "Snacks", "pkt", Decimal("28.00"), Decimal("35.00"), Decimal("40.00"), Decimal("10.00")),
            ("Surf Excel Easy Wash 1kg", "SURF-1KG", "Cleaning", "pkt", Decimal("120.00"), Decimal("145.00"), Decimal("20.00"), Decimal("5.00")),
            ("Lifebuoy Soap 125g", "SOAP-LIFE", "Personal Care", "pcs", Decimal("30.00"), Decimal("38.00"), Decimal("35.00"), Decimal("8.00")),
            ("Dettol Handwash 200ml", "DET-HW-200", "Personal Care", "btl", Decimal("80.00"), Decimal("99.00"), Decimal("1.00"), Decimal("5.00")), # Low stock
        ]

        products_map = {}
        for name, sku, cat, unit, cost, price, stock, threshold in products_data:
            p = Product(
                business_id=business.id,
                product_name=name,
                SKU=sku,
                category=cat,
                unit=unit,
                purchase_price=cost,
                selling_price=price,
                current_stock=stock,
                low_stock_threshold=threshold
            )
            db.add(p)
            db.flush()
            products_map[sku] = p

            inv_tx = InventoryTransaction(
                business_id=business.id,
                product_id=p.id,
                transaction_type="RESTOCK",
                quantity=stock,
                description="Demo opening inventory"
            )
            db.add(inv_tx)

        # 5. Create 10 Customers
        customers_data = [
            ("Ramesh Kumar", "9845012345", "12th Cross, Malleshwaram", Decimal("1250.00")),
            ("Suresh Gowda", "9845023456", "Margosa Road, Bengaluru", Decimal("450.00")),
            ("Priya Nair", "9845034567", "Srirampura, Bengaluru", Decimal("0.00")),
            ("Rajesh Sharma", "9845045678", "Vyalikaval, Bengaluru", Decimal("800.00")),
            ("Ananya Rao", "9845056789", "Sadashivanagar, Bengaluru", Decimal("0.00")),
            ("Mohammed Faizal", "9845067890", "Yeshwanthpur, Bengaluru", Decimal("2100.00")),
            ("Lakshmi Devi", "9845078901", "Subramanyanagar, Bengaluru", Decimal("320.00")),
            ("Venkatesh Prasad", "9845089012", "Mathikere, Bengaluru", Decimal("0.00")),
            ("Deepa Menon", "9845090123", "Rajajinagar 1st Block", Decimal("650.00")),
            ("Manoj Patil", "9845001234", "Mahalakshmi Layout", Decimal("0.00")),
        ]

        customers_map = {}
        for name, phone, addr, balance in customers_data:
            c = Customer(
                business_id=business.id,
                customer_name=name,
                phone=phone,
                address=addr,
                outstanding_balance=balance
            )
            db.add(c)
            db.flush()
            customers_map[name] = c

            if balance > 0:
                credit_tx = CreditTransaction(
                    business_id=business.id,
                    customer_id=c.id,
                    transaction_type="CREDIT_GIVEN",
                    amount=balance,
                    description="Opening credit balance"
                )
                db.add(credit_tx)

        # 6. Create Sales & SaleItems spanning last 7 days + today
        now = datetime.now(timezone.utc)
        inv_counter = 1

        # Historical sales (past 6 days)
        for days_ago in range(6, 0, -1):
            sale_date = now - timedelta(days=days_ago, hours=2)
            for idx in range(3):
                inv_no = f"INV-2026-{inv_counter:04d}"
                inv_counter += 1

                p1 = products_map["MILK-500"]
                p2 = products_map["SUG-1KG"]
                
                subtotal = (p1.selling_price * 2) + (p2.selling_price * 1)
                sale = Sale(
                    business_id=business.id,
                    customer_id=customers_map["Ramesh Kumar"].id if idx == 0 else None,
                    invoice_number=inv_no,
                    subtotal=subtotal,
                    discount=Decimal("0.00"),
                    tax=Decimal("0.00"),
                    total_amount=subtotal,
                    payment_method="Cash" if idx != 0 else "Credit",
                    payment_status="PAID" if idx != 0 else "UNPAID",
                    created_at=sale_date
                )
                db.add(sale)
                db.flush()

                item1 = SaleItem(
                    sale_id=sale.id,
                    product_id=p1.id,
                    quantity=Decimal("2.00"),
                    unit_price=p1.selling_price,
                    purchase_price_snapshot=p1.purchase_price,
                    total_amount=p1.selling_price * 2
                )
                item2 = SaleItem(
                    sale_id=sale.id,
                    product_id=p2.id,
                    quantity=Decimal("1.00"),
                    unit_price=p2.selling_price,
                    purchase_price_snapshot=p2.purchase_price,
                    total_amount=p2.selling_price * 1
                )
                db.add_all([item1, item2])

        # Today's sales
        today_sales_configs = [
            ("INV-2026-0019", "UPI", "PAID", None, [
                ("RICE-25KG", Decimal("1.00")),
                ("OIL-SUN-1L", Decimal("2.00")),
                ("SALT-1KG", Decimal("1.00"))
            ]),
            ("INV-2026-0020", "Cash", "PAID", None, [
                ("MILK-500", Decimal("3.00")),
                ("PARLE-250", Decimal("2.00")),
                ("TEA-500", Decimal("1.00"))
            ]),
            ("INV-2026-0021", "Credit", "UNPAID", "Suresh Gowda", [
                ("ATTA-10KG", Decimal("1.00")),
                ("DAL-TOOR", Decimal("2.00")),
                ("GHEE-500", Decimal("1.00"))
            ]),
            ("INV-2026-0022", "Cash", "PAID", None, [
                ("BUT-100", Decimal("2.00")),
                ("CURD-500", Decimal("2.00")),
                ("GOOD-DAY", Decimal("3.00"))
            ]),
        ]

        for inv_no, method, status, cust_name, items_list in today_sales_configs:
            subtotal = Decimal("0.00")
            sale_items = []
            for sku, qty in items_list:
                prod = products_map[sku]
                cost_tot = prod.selling_price * qty
                subtotal += cost_tot
                sale_items.append((prod, qty, prod.selling_price, prod.purchase_price, cost_tot))

            sale = Sale(
                business_id=business.id,
                customer_id=customers_map[cust_name].id if cust_name else None,
                invoice_number=inv_no,
                subtotal=subtotal,
                discount=Decimal("0.00"),
                tax=Decimal("0.00"),
                total_amount=subtotal,
                payment_method=method,
                payment_status=status,
                created_at=now - timedelta(minutes=45)
            )
            db.add(sale)
            db.flush()

            for prod, qty, u_price, p_snap, t_amt in sale_items:
                s_item = SaleItem(
                    sale_id=sale.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=u_price,
                    purchase_price_snapshot=p_snap,
                    total_amount=t_amt
                )
                db.add(s_item)

        # 7. Create Expenses
        expenses_data = [
            ("Electricity", "Electricity bill for shop - BESCOM", Decimal("1450.00"), "UPI", now - timedelta(days=2)),
            ("Transport", "Tempo freight for flour & grain delivery", Decimal("600.00"), "Cash", now - timedelta(days=1)),
            ("Miscellaneous", "Tea and snacks for helpers", Decimal("120.00"), "Cash", now - timedelta(hours=3)),
            ("Rent", "Monthly shop advance maintenance", Decimal("2000.00"), "Bank Transfer", now - timedelta(days=5)),
        ]

        for cat, desc, amt, method, dt in expenses_data:
            exp = Expense(
                business_id=business.id,
                category=cat,
                description=desc,
                amount=amt,
                payment_method=method,
                created_at=dt
            )
            db.add(exp)

        # 8. Repayment transaction
        repay = CreditTransaction(
            business_id=business.id,
            customer_id=customers_map["Ramesh Kumar"].id,
            transaction_type="REPAYMENT",
            amount=Decimal("500.00"),
            description="Partial cash repayment",
            created_at=now - timedelta(hours=5)
        )
        db.add(repay)

        db.commit()

        return {
            "status": "success",
            "message": "Demo data successfully seeded with 25 products, 10 customers, sales, credit ledger, and expenses.",
            "demo_credentials": {
                "email": DEMO_USER_EMAIL,
                "password": "demo12345"
            },
            "business": {
                "name": business.business_name,
                "gstin": business.GSTIN,
                "products_count": len(products_data),
                "customers_count": len(customers_data)
            }
        }

