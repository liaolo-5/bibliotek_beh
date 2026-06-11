import streamlit as st
import sqlite3

conn = sqlite3.connect("bibliotek.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    titel TEXT,
    forfattare TEXT,
    antal INTEGER,
    tillgangliga INTEGER,
    lantagare TEXT
)
""")

conn.commit()

ADMIN_PASSWORD = "211"

st.title("📚 BEH Bibliotek")
if "success_message" in st.session_state:
    st.success(st.session_state["success_message"])
    del st.session_state["success_message"]


def get_bibliotek():
    cursor.execute("""
    SELECT * FROM books
    ORDER BY titel COLLATE NOCASE
    """)

    rows = cursor.fetchall()

    bibliotek = {}

    for row in rows:
        bibliotek[row[0]] = {
            "titel": row[1],
            "författare": row[2],
            "antal": row[3],
            "tillgängliga": row[4],
            "låntagare": row[5].split(",") if row[5] else []
        }

    return bibliotek


def sorted_books(bibliotek):
    return sorted(bibliotek.items(), key=lambda x: x[1]["titel"])

bibliotek = get_bibliotek()


# --- SÖK ---
sok = st.text_input("🔍 Sök bok (titel eller författare)").lower().strip()

result = []
st.subheader("📖 Böcker i biblioteket")

for book_id, data in sorted_books(bibliotek):
    titel = str(data.get("titel", "")).lower()
    forfattare = str(data.get("författare", "")).lower()

    if sok and (sok not in titel and sok not in forfattare):
        continue

    with st.container():
        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(f"📘 {data['titel']}")
            st.write(f"✍️ {data['författare']}")
            st.write(f"📦 Tillgängliga: {data['tillgängliga']}")

        with col2:
            input_key = f"name_{book_id}"
        
            # init state
            if input_key not in st.session_state:
                st.session_state[input_key] = ""
        
            # RESET-logik (viktigt)
            if st.session_state.get(f"reset_{book_id}", False):
                st.session_state[input_key] = ""
                st.session_state[f"reset_{book_id}"] = False
        
            namn = st.text_input("Namn", key=input_key)
        
            if f"msg_{book_id}" in st.session_state:
                st.success(st.session_state[f"msg_{book_id}"])
                del st.session_state[f"msg_{book_id}"]
        
            if st.button("Låna", key=f"loan_{book_id}"):
        
                namn_clean = st.session_state.get(input_key, "").strip()
        
                if namn_clean == "":
                    st.warning("⚠️ Skriv namn först")
        
                elif data["tillgängliga"] <= 0:
                    st.error("❌ Boken är slut")
        
                else:
                    data["tillgängliga"] -= 1
                    data["låntagare"].append(namn_clean.title())
        
                    cursor.execute("""
                    UPDATE books
                    SET tillgangliga = ?,
                        lantagare = ?
                    WHERE id = ?
                    """, (
                        data["tillgängliga"],
                        ",".join(data["låntagare"]),
                        book_id,
                    ))
        
                    conn.commit()
        
                    st.session_state[f"msg_{book_id}"] = (
                        f"✅ {namn_clean.title()} lånade {data['titel']}"
                    )
        
                    # 🔥 istället för att skriva direkt till input
                    st.session_state[f"reset_{book_id}"] = True
        
                    st.rerun()

st.sidebar.header("🔁 Returnera bok")

# lista bara böcker som har låntagare
valbara_bocker = [
    f"{bid} - {data['titel']}"
    for bid, data in sorted_books(bibliotek)
    if len(data["låntagare"]) > 0
]

val_bok = st.sidebar.selectbox("Välj bok", valbara_bocker)

if val_bok:
    book_id = val_bok.split(" - ")[0]
    data = bibliotek[book_id]

    namn = st.sidebar.selectbox(
        "Vem ska returnera?",
        data["låntagare"],
        key="return_name"
    )

    if st.sidebar.button("Returnera", key="return_btn"):
        data["låntagare"].remove(namn)
        data["tillgängliga"] += 1

        cursor.execute("""
        UPDATE books
        SET tillgangliga = ?,
            lantagare = ?
        WHERE id = ?
        """, (
            data["tillgängliga"],
            ",".join(data["låntagare"]),
            book_id
        ))

        conn.commit()

        # ⭐ VISAS DIREKT I SIDEBAR
        st.sidebar.success(f"🔁 {namn} returnerade '{data['titel']}'")

        st.rerun()

st.sidebar.header("🔐 Admin")

password = st.sidebar.text_input("Lösenord", type="password")

if password == ADMIN_PASSWORD:
    st.sidebar.success("Åtkomst beviljad")

    st.sidebar.subheader("➕ Lägg till bok")

    titel = st.sidebar.text_input("Titel").title().strip()
    författare = st.sidebar.text_input("Författare").title().strip()
    antal = st.sidebar.number_input("Antal", min_value=1, step=1)

    if st.sidebar.button("Lägg till bok"):
    
        if not titel:
            st.sidebar.error("Titel saknas")
    
        elif not författare:
            st.sidebar.error("Författare saknas")
    
        else:
            cursor.execute("""
            SELECT id
            FROM books
            ORDER BY CAST(SUBSTR(id, 2) AS INTEGER) DESC
            LIMIT 1
            """)
    
            last = cursor.fetchone()
    
            if last:
                next_id = int(last[0][1:]) + 1
            else:
                next_id = 1
    
            book_id = f"B{next_id}"
    
            cursor.execute("""
            INSERT INTO books
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                book_id,
                titel,
                författare,
                int(antal),
                int(antal),
                ""
            ))
    
            conn.commit()
    
            st.sidebar.success(f"Bok tillagd: {titel}")
            st.rerun()

    st.sidebar.subheader("❌ Ta bort bok")

        # --- steg 1: välj bok ---
    remove_choice = st.sidebar.selectbox(
        "Välj bok att ta bort",
        [f"{bid} - {data['titel']}" for bid, data in sorted_books(bibliotek)],
        key="remove_select"
    )
    
    if remove_choice:
        book_id = remove_choice.split(" - ")[0]
        titel = bibliotek[book_id]["titel"]
    
        # --- klicka initiera delete ---
        if st.sidebar.button("🗑 Ta bort bok", key="delete_btn"):
            st.session_state["confirm_delete"] = book_id
    
    # --- steg 2: bekräftelse ---
    if "confirm_delete" in st.session_state:
        book_id = st.session_state["confirm_delete"]
        titel = bibliotek[book_id]["titel"]
    
        st.sidebar.warning(f"Är du säker på att du vill ta bort '{titel}'?")
    
        col1, col2 = st.sidebar.columns(2)
    
        with col1:
            if st.button("Ja, ta bort", key="confirm_delete_btn"):
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
                conn.commit()
                st.sidebar.success(f"{titel} borttagen")
    
                del st.session_state["confirm_delete"]
                st.rerun()

        with col2:
            if st.button("Avbryt", key="cancel_delete_btn"):
                st.sidebar.info("Avbrutet")

                del st.session_state["confirm_delete"]
                st.rerun()

    st.sidebar.subheader("✏️ Editera bok")

    edit_choice = st.sidebar.selectbox(
        "Välj bok att editera",
        [f"{bid} - {data['titel']}" for bid, data in sorted_books(bibliotek)],
        key="edit_select",
    )

    if edit_choice:
        book_id = edit_choice.split(" - ")[0]
        book = bibliotek[book_id]

        ny_titel = st.sidebar.text_input(
            "Titel", value=str(book.get("titel", "")), key=f"title_{book_id}"
        )

        ny_forfattare = st.sidebar.text_input(
            "Författare", value=str(book.get("författare", "")), key=f"author_{book_id}"
        )

        nytt_antal = st.sidebar.number_input(
            "Antal",
            min_value=1,
            value=int(book.get("antal", 1)),
            key=f"antal_{book_id}",
        )

        if st.sidebar.button("Spara ändringar"):

            skillnad = int(nytt_antal) - int(book["antal"])
        
            nytt_tillgangligt = max(
                0,
                int(book["tillgängliga"]) + skillnad
            )
        
            cursor.execute("""
            UPDATE books
            SET titel = ?,
                forfattare = ?,
                antal = ?,
                tillgangliga = ?
            WHERE id = ?
            """, (
                ny_titel,
                ny_forfattare,
                int(nytt_antal),
                nytt_tillgangligt,
                book_id
            ))
        
            conn.commit()
        
            st.sidebar.success("Boken uppdaterad!")
            st.rerun()

conn.close()
