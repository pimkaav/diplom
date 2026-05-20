from __future__ import annotations
from typing import Optional
from database.db_manager import DatabaseManager, hash_password


def _db():
    return DatabaseManager()


# ──────────────────────────── USERS ────────────────────────────

class UserModel:
    @staticmethod
    def login(username: str, password: str) -> Optional[dict]:
        pwd_hash = hash_password(password)
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username=%s AND password_hash=%s AND is_active=1",
                (username, pwd_hash),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def register(username: str, email: str, password: str, role: str,
                 full_name: str = "", phone: str = "", city: str = "") -> tuple[bool, str]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM users WHERE username=%s OR email=%s", (username, email)
            )
            if cur.fetchone():
                return False, "Пользователь с таким логином или email уже существует"
            cur.execute(
                "INSERT INTO users (username,email,password_hash,role,full_name,phone,city) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (username, email, hash_password(password), role, full_name, phone, city),
            )
        return True, "Регистрация успешна"

    @staticmethod
    def get_by_id(user_id: int) -> Optional[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_profile(user_id: int, full_name: str, phone: str, city: str, bio: str):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET full_name=%s,phone=%s,city=%s,bio=%s WHERE id=%s",
                (full_name, phone, city, bio, user_id),
            )

    @staticmethod
    def update_avatar(user_id: int, avatar_path: str):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET avatar_path=%s WHERE id=%s", (avatar_path, user_id))

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM users WHERE id=%s AND password_hash=%s",
                (user_id, hash_password(old_password)),
            )
            if not cur.fetchone():
                return False, "Неверный текущий пароль"
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (hash_password(new_password), user_id),
            )
        return True, "Пароль изменён"

    @staticmethod
    def get_all(role: Optional[str] = None) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            if role:
                cur.execute(
                    "SELECT * FROM users WHERE role=%s ORDER BY created_at DESC", (role,)
                )
            else:
                cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def set_active(user_id: int, is_active: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active=%s WHERE id=%s", (is_active, user_id))

    @staticmethod
    def update_rating(user_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE reviewed_user_id=%s",
                (user_id,),
            )
            row = cur.fetchone()
            cur.execute(
                "UPDATE users SET rating=%s,rating_count=%s WHERE id=%s",
                (round(row["avg_r"] or 0, 2), row["cnt"], user_id),
            )

    @staticmethod
    def get_balance(user_id: int) -> float:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
        return float(row["balance"]) if row else 0.0

    @staticmethod
    def add_balance(user_id: int, amount: float) -> float:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET balance = balance + %s WHERE id=%s", (amount, user_id)
            )
            cur.execute("SELECT balance FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
        return float(row["balance"])

    @staticmethod
    def subtract_balance(user_id: int, amount: float) -> tuple[bool, float]:
        """Deduct amount if sufficient balance. Returns (success, new_balance)."""
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
            if not row or float(row["balance"]) < amount:
                return False, float(row["balance"]) if row else 0.0
            cur.execute(
                "UPDATE users SET balance = balance - %s WHERE id=%s", (amount, user_id)
            )
            cur.execute("SELECT balance FROM users WHERE id=%s", (user_id,))
            new_bal = cur.fetchone()["balance"]
        return True, float(new_bal)


# ──────────────────────────── COMPANY ────────────────────────────

class CompanyModel:
    @staticmethod
    def get_by_user(user_id: int) -> Optional[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM company_profiles WHERE user_id=%s", (user_id,)
            )
            row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_id(cp_id: int) -> Optional[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT cp.*, u.username, u.full_name FROM company_profiles cp "
                "JOIN users u ON u.id=cp.user_id WHERE cp.id=%s", (cp_id,)
            )
            row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_all() -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT cp.*, u.username FROM company_profiles cp "
                "JOIN users u ON u.id=cp.user_id ORDER BY cp.rating DESC"
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def upsert(user_id: int, data: dict):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM company_profiles WHERE user_id=%s", (user_id,))
            if cur.fetchone():
                cur.execute(
                    """UPDATE company_profiles SET
                       company_name=%s,description=%s,truck_count=%s,truck_categories=%s,
                       price_per_km=%s,operating_cities=%s,phone=%s,email=%s,website=%s,
                       inn=%s,license_number=%s WHERE user_id=%s""",
                    (data["company_name"], data.get("description", ""),
                     data.get("truck_count", 0), data.get("truck_categories", ""),
                     data.get("price_per_km", 0), data.get("operating_cities", ""),
                     data.get("phone", ""), data.get("email", ""), data.get("website", ""),
                     data.get("inn", ""), data.get("license_number", ""), user_id),
                )
            else:
                cur.execute(
                    """INSERT INTO company_profiles
                       (user_id,company_name,description,truck_count,truck_categories,
                        price_per_km,operating_cities,phone,email,website,inn,license_number)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (user_id, data["company_name"], data.get("description", ""),
                     data.get("truck_count", 0), data.get("truck_categories", ""),
                     data.get("price_per_km", 0), data.get("operating_cities", ""),
                     data.get("phone", ""), data.get("email", ""), data.get("website", ""),
                     data.get("inn", ""), data.get("license_number", "")),
                )

    @staticmethod
    def update_rating(user_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT AVG(r.rating) as avg_r, COUNT(*) as cnt "
                "FROM reviews r WHERE r.reviewed_user_id=%s",
                (user_id,),
            )
            row = cur.fetchone()
            cur.execute(
                "UPDATE company_profiles SET rating=%s,rating_count=%s WHERE user_id=%s",
                (round(row["avg_r"] or 0, 2), row["cnt"], user_id),
            )

    @staticmethod
    def increment_completed(user_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE company_profiles SET completed_orders=completed_orders+1 WHERE user_id=%s",
                (user_id,),
            )

    @staticmethod
    def set_verified(company_id: int, is_verified: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE company_profiles SET is_verified=%s WHERE id=%s", (is_verified, company_id)
            )


# ──────────────────────────── TRUCKS ────────────────────────────

class TruckModel:
    @staticmethod
    def get_by_carrier(carrier_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM trucks WHERE carrier_id=%s ORDER BY brand, model",
                (carrier_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(carrier_id: int, brand: str, model: str, year: Optional[int],
            plate_number: str, cargo_type: str,
            capacity_tons: float, volume_m3: float) -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO trucks
                   (carrier_id,brand,model,year,plate_number,cargo_type,capacity_tons,volume_m3)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (carrier_id, brand, model, year, plate_number, cargo_type, capacity_tons, volume_m3),
            )
            return cur.fetchone()["id"]

    @staticmethod
    def delete(truck_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM trucks WHERE id=%s", (truck_id,))

    @staticmethod
    def set_available(truck_id: int, available: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE trucks SET is_available=%s WHERE id=%s", (available, truck_id))

    @staticmethod
    def count(carrier_id: int) -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM trucks WHERE carrier_id=%s", (carrier_id,)
            )
            return cur.fetchone()["cnt"]


# ──────────────────────────── ORDERS ────────────────────────────

class OrderModel:
    @staticmethod
    def create(data: dict) -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO orders
                   (customer_id,title,cargo_type,cargo_weight,cargo_volume,
                    from_city,to_city,from_address,to_address,from_lat,from_lng,to_lat,to_lng,
                    distance,pickup_date,delivery_date,budget,comment,special_requirements,
                    invited_carrier_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id""",
                (data["customer_id"], data["title"], data.get("cargo_type", ""),
                 data.get("cargo_weight", 0), data.get("cargo_volume", 0),
                 data["from_city"], data["to_city"],
                 data.get("from_address", ""), data.get("to_address", ""),
                 data.get("from_lat"), data.get("from_lng"),
                 data.get("to_lat"), data.get("to_lng"),
                 data.get("distance", 0),
                 data["pickup_date"], data.get("delivery_date", ""),
                 data.get("budget", 0), data.get("comment", ""),
                 data.get("special_requirements", ""),
                 data.get("invited_carrier_id")),
            )
            return cur.fetchone()["id"]

    @staticmethod
    def get_by_customer(customer_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT o.*, u.full_name as carrier_name FROM orders o "
                "LEFT JOIN users u ON u.id=o.carrier_id "
                "WHERE o.customer_id=%s ORDER BY o.created_at DESC",
                (customer_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_available() -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT o.*, u.full_name as customer_name, u.phone as customer_phone "
                "FROM orders o JOIN users u ON u.id=o.customer_id "
                "WHERE o.status='new' ORDER BY o.created_at DESC"
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_carrier(carrier_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT o.*, u.full_name as customer_name, u.phone as customer_phone "
                "FROM orders o JOIN users u ON u.id=o.customer_id "
                "WHERE o.carrier_id=%s ORDER BY o.updated_at DESC",
                (carrier_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(order_id: int) -> Optional[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT o.*, u.full_name as customer_name, u.phone as customer_phone, "
                "u.email as customer_email "
                "FROM orders o JOIN users u ON u.id=o.customer_id WHERE o.id=%s",
                (order_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_all() -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT o.*, uc.full_name as customer_name, uc2.full_name as carrier_name "
                "FROM orders o "
                "JOIN users uc ON uc.id=o.customer_id "
                "LEFT JOIN users uc2 ON uc2.id=o.carrier_id "
                "ORDER BY o.created_at DESC"
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def update_status(order_id: int, status: str, carrier_id: Optional[int] = None):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            if carrier_id is not None:
                cur.execute(
                    "UPDATE orders SET status=%s,carrier_id=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                    (status, carrier_id, order_id),
                )
            else:
                cur.execute(
                    "UPDATE orders SET status=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                    (status, order_id),
                )

    @staticmethod
    def update_progress(order_id: int, progress_status: str):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE orders SET progress_status=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (progress_status, order_id),
            )

    @staticmethod
    def assign_vehicle(order_id: int, driver_name: str, truck_number: str, truck_model: str):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE orders SET driver_name=%s,truck_number=%s,truck_model=%s,
                   progress_status='vehicle_assigned',updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                (driver_name, truck_number, truck_model, order_id),
            )

    @staticmethod
    def confirm_dispatch(order_id: int):
        """Customer confirms cargo was picked up → payment held."""
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE orders SET dispatch_confirmed_by_customer=1,
                   dispatch_confirmed_at=CURRENT_TIMESTAMP,
                   progress_status='in_transit',
                   updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                (order_id,),
            )

    @staticmethod
    def mark_dispatched_by_carrier(order_id: int):
        """Carrier marks cargo as dispatched."""
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE orders SET progress_status='dispatched',
                   updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                (order_id,),
            )

    @staticmethod
    def mark_arrived_by_carrier(order_id: int):
        """Carrier marks arrival at destination."""
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE orders SET progress_status='arrived',
                   updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                (order_id,),
            )

    @staticmethod
    def confirm_arrival(order_id: int):
        """Customer confirms receipt → payment released, order completed."""
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE orders SET arrival_confirmed_by_customer=1,
                   arrival_confirmed_at=CURRENT_TIMESTAMP,
                   progress_status='completed',
                   status='completed',
                   updated_at=CURRENT_TIMESTAMP WHERE id=%s""",
                (order_id,),
            )

    @staticmethod
    def stats() -> dict:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM orders")
            total = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM orders WHERE status='new'")
            new_cnt = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM orders WHERE status='in_progress'")
            in_prog = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM orders WHERE status='completed'")
            done = cur.fetchone()["cnt"]
        return {"total": total, "new": new_cnt, "in_progress": in_prog, "completed": done}

    @staticmethod
    def invite_carrier(order_id: int, carrier_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE orders SET invited_carrier_id=%s WHERE id=%s",
                (carrier_id, order_id),
            )


# ──────────────────────────── RESPONSES ────────────────────────────

class ResponseModel:
    @staticmethod
    def create(order_id: int, carrier_id: int, message: str,
               proposed_cost: float, estimated_days: int) -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO order_responses "
                "(order_id,carrier_id,message,proposed_cost,estimated_days) "
                "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (order_id, carrier_id, message, proposed_cost, estimated_days),
            )
            return cur.fetchone()["id"]

    @staticmethod
    def get_by_order(order_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT r.*, u.full_name as carrier_name, u.phone as carrier_phone,
                   cp.company_name, cp.rating as company_rating
                   FROM order_responses r JOIN users u ON u.id=r.carrier_id
                   LEFT JOIN company_profiles cp ON cp.user_id=r.carrier_id
                   WHERE r.order_id=%s ORDER BY r.created_at DESC""",
                (order_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_carrier(carrier_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT r.*, o.title, o.from_city, o.to_city, o.pickup_date
                   FROM order_responses r JOIN orders o ON o.id=r.order_id
                   WHERE r.carrier_id=%s ORDER BY r.created_at DESC""",
                (carrier_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def update_status(response_id: int, status: str):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE order_responses SET status=%s WHERE id=%s", (status, response_id)
            )

    @staticmethod
    def already_responded(order_id: int, carrier_id: int) -> bool:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM order_responses WHERE order_id=%s AND carrier_id=%s",
                (order_id, carrier_id),
            )
            return cur.fetchone() is not None


# ──────────────────────────── REVIEWS ────────────────────────────

class ReviewModel:
    @staticmethod
    def create(reviewer_id: int, reviewed_user_id: int,
               order_id: Optional[int], rating: int, comment: str):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO reviews (reviewer_id,reviewed_user_id,order_id,rating,comment) "
                "VALUES (%s,%s,%s,%s,%s)",
                (reviewer_id, reviewed_user_id, order_id, rating, comment),
            )
        UserModel.update_rating(reviewed_user_id)
        CompanyModel.update_rating(reviewed_user_id)

    @staticmethod
    def get_by_user(user_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT r.*, u.full_name as reviewer_name, u.avatar_path
                   FROM reviews r JOIN users u ON u.id=r.reviewer_id
                   WHERE r.reviewed_user_id=%s ORDER BY r.created_at DESC""",
                (user_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def already_reviewed(reviewer_id: int, reviewed_user_id: int, order_id: int) -> bool:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM reviews WHERE reviewer_id=%s AND reviewed_user_id=%s AND order_id=%s",
                (reviewer_id, reviewed_user_id, order_id),
            )
            return cur.fetchone() is not None


# ──────────────────────────── MESSAGES ────────────────────────────

class MessageModel:
    @staticmethod
    def send(sender_id: int, receiver_id: int, content: str,
             order_id: Optional[int] = None, attachment_path: str = "") -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO messages (sender_id,receiver_id,order_id,content,attachment_path) "
                "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (sender_id, receiver_id, order_id, content, attachment_path),
            )
            msg_id = cur.fetchone()["id"]
        NotificationModel.create(
            receiver_id, "message", "Новое сообщение", "У вас новое сообщение", msg_id
        )
        return msg_id

    @staticmethod
    def get_conversation(user1_id: int, user2_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT m.*, u.full_name as sender_name, u.avatar_path
                   FROM messages m JOIN users u ON u.id=m.sender_id
                   WHERE (m.sender_id=%s AND m.receiver_id=%s)
                      OR (m.sender_id=%s AND m.receiver_id=%s)
                   ORDER BY m.created_at ASC""",
                (user1_id, user2_id, user2_id, user1_id),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def mark_read(sender_id: int, receiver_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE messages SET is_read=1 WHERE sender_id=%s AND receiver_id=%s AND is_read=0",
                (sender_id, receiver_id),
            )

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE receiver_id=%s AND is_read=0",
                (user_id,),
            )
            return cur.fetchone()["cnt"]

    @staticmethod
    def get_contacts(user_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """WITH contacts AS (
                       SELECT
                           CASE WHEN m.sender_id=%(uid)s THEN m.receiver_id
                                ELSE m.sender_id END AS contact_id,
                           u.full_name, u.avatar_path, u.role,
                           m.created_at,
                           CASE WHEN m.receiver_id=%(uid)s AND m.is_read=0 THEN 1 ELSE 0 END AS is_unread
                       FROM messages m
                       JOIN users u ON u.id = CASE WHEN m.sender_id=%(uid)s
                                                   THEN m.receiver_id
                                                   ELSE m.sender_id END
                       WHERE m.sender_id=%(uid)s OR m.receiver_id=%(uid)s
                   )
                   SELECT contact_id, full_name, avatar_path, role,
                          MAX(created_at) as last_msg_time,
                          SUM(is_unread) as unread
                   FROM contacts
                   GROUP BY contact_id, full_name, avatar_path, role
                   ORDER BY last_msg_time DESC""",
                {"uid": user_id},
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]


# ──────────────────────────── NOTIFICATIONS ────────────────────────────

class NotificationModel:
    @staticmethod
    def create(user_id: int, ntype: str, title: str,
               message: str = "", related_id: Optional[int] = None):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notifications (user_id,type,title,message,related_id) "
                "VALUES (%s,%s,%s,%s,%s)",
                (user_id, ntype, title, message, related_id),
            )

    @staticmethod
    def get_by_user(user_id: int) -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 60",
                (user_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM notifications WHERE user_id=%s AND is_read=0",
                (user_id,),
            )
            return cur.fetchone()["cnt"]

    @staticmethod
    def mark_read(notification_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE notifications SET is_read=1 WHERE id=%s", (notification_id,)
            )

    @staticmethod
    def mark_all_read(user_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE notifications SET is_read=1 WHERE user_id=%s", (user_id,)
            )


# ──────────────────────────── PAYMENTS ────────────────────────────

class PaymentModel:
    @staticmethod
    def create(order_id: int, amount: float, payer_id: int, receiver_id: int) -> Optional[int]:
        import uuid
        tx_id = str(uuid.uuid4())[:16].upper()
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO payments
                   (order_id,amount,payer_id,receiver_id,transaction_id,status)
                   VALUES (%s,%s,%s,%s,%s,'pending')
                   ON CONFLICT DO NOTHING RETURNING id""",
                (order_id, amount, payer_id, receiver_id, tx_id),
            )
            row = cur.fetchone()
            return row["id"] if row else None

    @staticmethod
    def get_by_order(order_id: int) -> Optional[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM payments WHERE order_id=%s", (order_id,))
            row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def hold(payment_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE payments SET status='held',held_at=CURRENT_TIMESTAMP WHERE id=%s",
                (payment_id,),
            )

    @staticmethod
    def release(payment_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE payments SET status='released',released_at=CURRENT_TIMESTAMP WHERE id=%s",
                (payment_id,),
            )

    @staticmethod
    def refund(payment_id: int):
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE payments SET status='refunded' WHERE id=%s", (payment_id,)
            )

    @staticmethod
    def get_all() -> list[dict]:
        with _db().get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT p.*, o.title as order_title,
                   up.full_name as payer_name, ur.full_name as receiver_name
                   FROM payments p
                   JOIN orders o ON o.id=p.order_id
                   JOIN users up ON up.id=p.payer_id
                   JOIN users ur ON ur.id=p.receiver_id
                   ORDER BY p.created_at DESC"""
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]
