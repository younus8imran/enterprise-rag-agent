import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.logging import logger


async def seed_database():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        logger.info("starting_seed_process")

        # 1. Create Tenant
        await conn.execute(text("INSERT INTO tenants (name, plan_level) VALUES ('Synthetic Corp', 'enterprise')"))
        tenant_id = 1

        # 2. Create Regions
        regions = ["North America", "EMEA", "APAC", "LATAM"]
        for r in regions:
            await conn.execute(text("INSERT INTO regions (name) VALUES (:name)"), {"name": r})

        # 3. Create Departments
        depts = ["Sales", "Engineering", "Marketing", "Human Resources", "Finance", "Operations"]
        for d in depts:
            await conn.execute(
                text("INSERT INTO departments (name, region_id) VALUES (:name, :rid)"),
                {"name": d, "rid": random.randint(1, 4)}
            )

        # 4. Create Employees
        names = ["Alice Smith", "Bob Johnson", "Charlie Brown", "Diana Prince", "Edward Norton", "Fiona Glenanne"]
        roles = ["Manager", "Lead", "Senior", "Junior", "Associate"]
        for name in names:
            await conn.execute(
                text("INSERT INTO employees (tenant_id, dept_id, full_name, email, role, salary) "
                     "VALUES (:tid, :did, :name, :email, :role, :salary)"),
                {
                    "tid": tenant_id,
                    "did": random.randint(1, 6),
                    "name": name,
                    "email": f"{name.lower().replace(' ', '.')}@syntheticcorp.com",
                    "role": random.choice(roles),
                    "salary": Decimal(random.randint(50000, 150000))
                }
            )

        # 5. Create Products
        categories = {"Electronics": ["Laptop", "Monitor", "Keyboard"], "Software": ["Cloud Suite", "IDE License", "Security Pack"], "Hardware": ["Server Rack", "Switch", "UPS"]}
        sku_counter = 1000
        for cat, prods in categories.items():
            for p_name in prods:
                sku_counter += 1
                await conn.execute(
                    text("INSERT INTO products (tenant_id, sku, name, category, unit_price, description) "
                         "VALUES (:tid, :sku, :name, :cat, :price, :desc)"),
                    {
                        "tid": tenant_id,
                        "sku": f"SYN-{sku_counter}",
                        "name": p_name,
                        "cat": cat,
                        "price": Decimal(random.randint(100, 5000)),
                        "desc": f"Enterprise grade {p_name} for high-scale operations."
                    }
                )

        # 6. Create Customers
        customer_names = ["GlobalLogistics", "TechNova", "OmniRetail", "ApexFinance", "EcoEnergy"]
        segments = ["Strategic", "Growth", "Transactional"]
        for cn in customer_names:
            await conn.execute(
                text("INSERT INTO customers (tenant_id, company_name, contact_email, segment, region_id) "
                     "VALUES (:tid, :name, :email, :seg, :rid)"),
                {
                    "tid": tenant_id,
                    "name": cn,
                    "email": f"contact@{cn.lower()}.com",
                    "seg": random.choice(segments),
                    "rid": random.randint(1, 4)
                }
            )

        # 7. Create Orders & OrderItems
        # Get product IDs first
        prod_res = await conn.execute(text("SELECT id, unit_price FROM products"))
        products = prod_res.all()

        for c_id in range(1, 6):
            num_orders = random.randint(2, 5)
            for _ in range(num_orders):
                # Insert order and get ID
                res = await conn.execute(
                    text("INSERT INTO orders (tenant_id, customer_id, order_date, status, total_amount) "
                         "VALUES (:tid, :cid, :date, :status, 0) RETURNING id"),
                    {
                        "tid": tenant_id,
                        "cid": c_id,
                        "date": datetime.now() - timedelta(days=random.randint(1, 365)),
                        "status": random.choice(["Completed", "Shipped", "Pending"])
                    }
                )
                order_id = res.scalar()

                # Add items
                order_total = Decimal(0)
                num_items = random.randint(1, 4)
                for _ in range(num_items):
                    prod_id, price = random.choice(products)
                    qty = random.randint(1, 10)
                    item_total = price * qty
                    order_total += item_total
                    await conn.execute(
                        text("INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
                             "VALUES (:oid, :pid, :qty, :price)"),
                        {"oid": order_id, "pid": prod_id, "qty": qty, "price": price}
                    )

                # Update order total
                await conn.execute(
                    text("UPDATE orders SET total_amount = :total WHERE id = :id"),
                    {"total": order_total, "id": order_id}
                )

        # 8. Create Expenses
        expense_cats = ["Travel", "Hardware", "Software Licenses", "Office Supplies", "Utilities"]
        for _ in range(50):
            await conn.execute(
                text("INSERT INTO expenses (tenant_id, dept_id, category, amount, expense_date, description) "
                     "VALUES (:tid, :did, :cat, :amt, :date, :desc)"),
                {
                    "tid": tenant_id,
                    "did": random.randint(1, 6),
                    "cat": random.choice(expense_cats),
                    "amt": Decimal(random.randint(50, 10000)),
                    "date": datetime.now() - timedelta(days=random.randint(1, 730)),
                    "desc": "Synthetic operational expense"
                }
            )

        logger.info("seed_complete")

if __name__ == "__main__":
    asyncio.run(seed_database())
